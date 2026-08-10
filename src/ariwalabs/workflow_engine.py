from pathlib import Path
from typing import Any

from .config import load_yaml

StepResult = dict[str, Any]
RECOVERABLE_MODEL_STATUSES = {
    "incomplete",
    "invalid_output",
    "provider_failed",
    "refused",
}

INTERNAL_ACTIONS = {
    "consolidate_validation_report",
    "persist_artifacts",
    "persist_draft_opportunity",
    "persist_report",
    "persist_state",
    "run_tests",
}
EXTERNAL_ACTION_TERMS = {
    "contact",
    "message",
    "payment",
    "publish",
}


class WorkflowEngine:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def run(
        self,
        *,
        agent_id: str,
        workflow_id: str,
        request_input: dict[str, Any],
    ) -> dict[str, Any]:
        agent_path = self.root / "agents" / agent_id
        workflow = load_yaml(agent_path / "workflows" / f"{workflow_id}.yaml").get("workflow", {})
        context = {
            "agent_id": agent_id,
            "request_input": request_input,
            "paused": False,
            "blocked": False,
            "needs_structured_output_review": False,
            "approval": None,
            "errors": [],
            "structured_output_error": None,
        }
        steps = self._run_steps(
            agent_id=agent_id,
            steps=workflow.get("steps", []),
            context=context,
            path_prefix=[],
        )
        status = self._status(context)
        return {
            "workflow_id": workflow_id,
            "status": status,
            "steps": steps,
            "errors": context["errors"],
            "approval": context["approval"],
            "structured_output_error": context["structured_output_error"],
        }

    def _run_steps(
        self,
        *,
        agent_id: str,
        steps: Any,
        context: dict[str, Any],
        path_prefix: list[int],
    ) -> list[StepResult]:
        if not isinstance(steps, list):
            context["blocked"] = True
            context["errors"].append("workflow.steps debe ser lista")
            return []

        results: list[StepResult] = []
        for index, step in enumerate(steps):
            if context["paused"] or context["blocked"]:
                break
            result = self._run_step(
                agent_id=agent_id,
                step=step,
                context=context,
                path=path_prefix + [index],
            )
            results.append(result)
        return results

    def _run_step(
        self,
        *,
        agent_id: str,
        step: Any,
        context: dict[str, Any],
        path: list[int],
    ) -> StepResult:
        if not isinstance(step, dict):
            return self._block(context, path, "unknown", "step debe ser objeto")

        if "condition" in step:
            return self._run_condition(agent_id, step, context, path)

        step_types = [
            key
            for key in ("skill", "parallel", "approval", "action", "workflow")
            if key in step
        ]
        if len(step_types) != 1:
            return self._block(context, path, "unknown", "step debe tener exactamente un tipo")

        step_type = step_types[0]
        if step_type == "skill":
            return self._run_skill(agent_id, step, context, path)
        if step_type == "parallel":
            return self._run_parallel(agent_id, step, context, path)
        if step_type == "approval":
            return self._run_approval(step, context, path)
        if step_type == "action":
            return self._run_action(step, context, path)
        return self._run_workflow(agent_id, step, context, path)

    def _run_skill(
        self,
        agent_id: str,
        step: dict[str, Any],
        context: dict[str, Any],
        path: list[int],
    ) -> StepResult:
        skill_id = step["skill"]
        if not isinstance(skill_id, str):
            return self._block(context, path, "skill", "skill debe ser string")
        if not self._skill_exists(agent_id, skill_id):
            return self._block(context, path, "skill", f"skill inexistente {skill_id}")
        model_result = self._model_result_for_skill(context["request_input"], skill_id)
        if model_result is not None:
            status = model_result.get("status")
            if status in RECOVERABLE_MODEL_STATUSES:
                return self._pause_for_structured_output_review(
                    context=context,
                    path=path,
                    skill_id=skill_id,
                    model_result=model_result,
                )
            return {
                "path": path,
                "type": "skill",
                "ref": skill_id,
                "status": "completed",
                "model_result": model_result,
            }
        return {
            "path": path,
            "type": "skill",
            "ref": skill_id,
            "status": "simulated",
        }

    def _run_parallel(
        self,
        agent_id: str,
        step: dict[str, Any],
        context: dict[str, Any],
        path: list[int],
    ) -> StepResult:
        branches = step["parallel"]
        if not isinstance(branches, list) or not branches:
            return self._block(context, path, "parallel", "parallel debe ser lista no vacia")
        branch_results = []
        for branch_index, branch in enumerate(branches):
            if context["blocked"]:
                break
            branch_result = self._run_step(
                agent_id=agent_id,
                step=branch,
                context=context,
                path=path + [branch_index],
            )
            branch_results.append(branch_result)
        return {
            "path": path,
            "type": "parallel",
            "status": "simulated" if not context["blocked"] else "blocked",
            "branches": branch_results,
        }

    def _run_condition(
        self,
        agent_id: str,
        step: dict[str, Any],
        context: dict[str, Any],
        path: list[int],
    ) -> StepResult:
        condition = step["condition"]
        if not isinstance(condition, str):
            return self._block(context, path, "condition", "condition debe ser string")
        if not self._condition_matches(condition, context["request_input"]):
            return {
                "path": path,
                "type": "condition",
                "condition": condition,
                "status": "skipped",
            }
        nested_step = {key: value for key, value in step.items() if key != "condition"}
        nested_result = self._run_step(
            agent_id=agent_id,
            step=nested_step,
            context=context,
            path=path + [0],
        )
        return {
            "path": path,
            "type": "condition",
            "condition": condition,
            "status": nested_result["status"],
            "step": nested_result,
        }

    def _run_approval(
        self,
        step: dict[str, Any],
        context: dict[str, Any],
        path: list[int],
    ) -> StepResult:
        approver = step["approval"]
        checkpoint = step.get("checkpoint")
        if approver != "company-director":
            return self._block(context, path, "approval", "approval debe ser company-director")
        if not isinstance(checkpoint, str) or not checkpoint:
            return self._block(context, path, "approval", "checkpoint requerido")
        context["paused"] = True
        context["approval"] = {
            "required": True,
            "status": "pending",
            "approver": approver,
            "checkpoint": checkpoint,
        }
        return {
            "path": path,
            "type": "approval",
            "checkpoint": checkpoint,
            "approver": approver,
            "status": "pending",
        }

    def _run_action(
        self,
        step: dict[str, Any],
        context: dict[str, Any],
        path: list[int],
    ) -> StepResult:
        action = step["action"]
        if not isinstance(action, str):
            return self._block(context, path, "action", "action debe ser string")
        if self._is_external_action(action):
            return self._block(context, path, "action", f"accion externa prohibida {action}")
        if action not in INTERNAL_ACTIONS:
            return self._block(context, path, "action", f"accion interna desconocida {action}")
        return {
            "path": path,
            "type": "action",
            "action": action,
            "status": "simulated",
        }

    def _run_workflow(
        self,
        agent_id: str,
        step: dict[str, Any],
        context: dict[str, Any],
        path: list[int],
    ) -> StepResult:
        workflow_id = step["workflow"]
        if not isinstance(workflow_id, str):
            return self._block(context, path, "workflow", "workflow debe ser string")
        workflow_path = self.root / "agents" / agent_id / "workflows" / f"{workflow_id}.yaml"
        if not workflow_path.exists():
            return self._block(context, path, "workflow", f"workflow inexistente {workflow_id}")
        workflow = load_yaml(workflow_path).get("workflow", {})
        steps = self._run_steps(
            agent_id=agent_id,
            steps=workflow.get("steps", []),
            context=context,
            path_prefix=path,
        )
        return {
            "path": path,
            "type": "workflow",
            "workflow_id": workflow_id,
            "status": self._status(context),
            "steps": steps,
        }

    def _skill_exists(self, agent_id: str, skill_id: str) -> bool:
        agent_path = self.root / "agents" / agent_id
        for skill_path in agent_path.glob("skills/*/skill.yaml"):
            skill = load_yaml(skill_path).get("skill", {})
            if skill.get("id") == skill_id:
                return True
        return False

    def _condition_matches(self, condition: str, request_input: dict[str, Any]) -> bool:
        return bool(request_input.get(condition))

    def _is_external_action(self, action: str) -> bool:
        return any(term in action for term in EXTERNAL_ACTION_TERMS)

    def _model_result_for_skill(
        self,
        request_input: dict[str, Any],
        skill_id: str,
    ) -> dict[str, Any] | None:
        skill_results = request_input.get("__skill_results__")
        if not isinstance(skill_results, dict):
            return None
        result = skill_results.get(skill_id)
        return result if isinstance(result, dict) else None

    def _pause_for_structured_output_review(
        self,
        *,
        context: dict[str, Any],
        path: list[int],
        skill_id: str,
        model_result: dict[str, Any],
    ) -> StepResult:
        status = str(model_result.get("status", "invalid_output"))
        raw_error = model_result.get("error")
        error = raw_error if isinstance(raw_error, dict) else {}
        structured_error = {
            "type": error.get("type", "ModelOutputError"),
            "message": error.get("message", "structured output invalido"),
            "retryable": bool(error.get("retryable", True)),
            "skill_id": skill_id,
            "status": status,
        }
        context["paused"] = True
        context["needs_structured_output_review"] = True
        context["structured_output_error"] = structured_error
        context["errors"].append(structured_error)
        return {
            "path": path,
            "type": "skill",
            "ref": skill_id,
            "status": "failed_recoverable",
            "model_result": {
                "status": status,
                "profile": model_result.get("profile"),
                "provider": model_result.get("provider"),
                "model": model_result.get("model"),
                "error": structured_error,
            },
        }

    def _block(
        self,
        context: dict[str, Any],
        path: list[int],
        step_type: str,
        message: str,
    ) -> StepResult:
        context["blocked"] = True
        context["errors"].append(message)
        return {
            "path": path,
            "type": step_type,
            "status": "blocked",
            "error": message,
        }

    def _status(self, context: dict[str, Any]) -> str:
        if context["blocked"]:
            return "blocked"
        if context["needs_structured_output_review"]:
            return "needs_structured_output_review"
        if context["paused"]:
            return "paused_for_approval"
        return "completed"
