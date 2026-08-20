from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from adapters.models.factory import create_model_adapter

from .approval_engine import ApprovalEngine
from .artifact_manager import ArtifactManager
from .audit import AuditLogger
from .business_packs import BusinessPackRegistry
from .config import load_yaml
from .context_engine import ContextEngine
from .errors import AgentNotFoundError, RequestValidationError, WorkflowNotFoundError
from .evaluation_engine import EvaluationEngine, EvaluationModelGateway
from .idempotency import (
    IdempotencyConflictError,
    fingerprint_request,
    idempotency_key_for_request,
    idempotency_storage_id,
    replay_execution,
)
from .model_gateway import ModelGateway
from .repository import JsonRepository
from .skill_executor import SkillExecutor
from .workflow_engine import WorkflowEngine

ACTION_ARTIFACT_TYPES = {
    "consolidate_validation_report": "framework_validation_report",
    "persist_artifacts": "workflow_artifacts",
    "persist_draft_opportunity": "draft_opportunity",
    "persist_report": "growth_report",
    "persist_state": "journey_state",
}


class AgentRuntime:
    def __init__(
        self,
        root: Path,
        *,
        business_pack_id: str | None = None,
        evaluation_model_gateway: EvaluationModelGateway | None = None,
        model_gateway: ModelGateway | None = None,
        execute_skills: bool = True,
    ):
        self.root = root
        self.business_pack_id = business_pack_id
        self.business_packs = BusinessPackRegistry(root)
        self.repo = JsonRepository(root / "runtime/data")
        self.audit = AuditLogger(root / "runtime/data/audit.jsonl")
        self.evaluation_model_gateway = evaluation_model_gateway
        self.model_gateway = model_gateway
        self.execute_skills = execute_skills

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        started_at = perf_counter()
        self._validate_run_request(request)
        agent_id = str(request["agent_id"])
        business_pack_id = request.get("business_pack_id")
        if not isinstance(business_pack_id, str):
            business_pack_id = self.business_pack_id
        agent_path = self.business_packs.agent_path(agent_id, business_pack_id)
        if not agent_path.exists():
            msg = f"agente inexistente {agent_id}"
            raise AgentNotFoundError(msg)
        config = load_yaml(agent_path / "agent.yaml")["agent"]
        workflow_id = str(request["workflow_id"])
        workflow_path = agent_path / "workflows" / f"{workflow_id}.yaml"
        if not workflow_path.exists():
            msg = f"workflow inexistente {workflow_id}"
            raise WorkflowNotFoundError(msg)
        workflow = load_yaml(workflow_path)
        composed_context = ContextEngine(
            self.root,
            business_pack_id=business_pack_id,
        ).compose_for_agent_workflow(
            agent_id=agent_id,
            workflow_id=workflow_id,
        )
        idempotency_key = idempotency_key_for_request(request)
        request_fingerprint = fingerprint_request(request)
        existing_execution = self._find_idempotent_execution(
            key=idempotency_key,
            fingerprint=request_fingerprint,
            agent_id=agent_id,
            workflow_id=workflow_id,
            actor=request["requested_by"],
        )
        if existing_execution is not None:
            return existing_execution
        execution_id = f"exec-{uuid4().hex[:12]}"
        requested_by = request["requested_by"]
        self.audit.execution(
            "agent.execution.started",
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            status="started",
            actor=requested_by,
        )
        try:
            workflow_execution = WorkflowEngine(
                self.root,
                business_pack_id=business_pack_id,
                skill_executor=self._skill_executor(
                    business_pack_id=business_pack_id,
                    composed_context=composed_context.to_dict(),
                    execution_id=execution_id,
                ),
                composed_context=composed_context.to_dict(),
                correlation_id=execution_id,
            ).run(
                agent_id=agent_id,
                workflow_id=workflow_id,
                request_input=request.get("input", {}),
            )
        except Exception as exc:
            self.audit.error(
                "agent.execution.error",
                error_type=exc.__class__.__name__,
                message=str(exc),
                actor=requested_by,
                correlation_id=execution_id,
                metadata={"agent_id": agent_id, "workflow_id": workflow_id},
            )
            raise
        evaluation = EvaluationEngine(
            self.root,
            business_pack_id=business_pack_id,
            model_gateway=self.evaluation_model_gateway,
        ).evaluate_workflow(
            agent_id=agent_id,
            workflow_id=workflow_id,
            workflow_execution=workflow_execution,
            correlation_id=execution_id,
        )
        approval = workflow_execution["approval"] or {
            "required": False,
            "status": "not_required",
            "approver": None,
            "checkpoint": None,
        }
        if workflow_execution["status"] == "paused_for_approval":
            pending_approval = ApprovalEngine(self.root).create_pending(
                execution_id=execution_id,
                agent_id=agent_id,
                workflow_id=workflow_id,
                checkpoint=approval["checkpoint"],
                approver=approval["approver"],
            )
            approval = {
                **approval,
                "approval_id": pending_approval["approval_id"],
            }
        structured_output_error = workflow_execution.get("structured_output_error")
        result = {
            "execution_id": execution_id,
            "agent_id": agent_id,
            "agent_version": config["version"],
            "workflow_id": workflow_id,
            "business_pack_id": business_pack_id,
            "requested_by": requested_by,
            "created_at": datetime.now(UTC).isoformat(),
            "status": "pending_human_approval",
            "input": request.get("input", {}),
            "workflow_definition": workflow,
            "workflow_execution": workflow_execution,
            "evaluation": evaluation,
            "shared_context": config.get("shared_context", []),
            "composed_context": composed_context.to_dict(),
            "approval": approval,
            "structured_output_error": structured_output_error,
            "idempotency": {
                "key": idempotency_key,
                "fingerprint": request_fingerprint,
                "replayed": False,
            },
        }
        result["status"] = self._execution_status(workflow_execution)
        result["artifacts"] = self._create_artifacts(
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            workflow_execution=workflow_execution,
            approval=approval,
        )
        path = self.repo.save("executions", execution_id, result)
        self.audit.execution(
            "agent.execution.created",
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            status=result["status"],
            actor=requested_by,
            metadata={"persistence_path": str(path.relative_to(self.root))},
        )
        if result["status"] == "completed":
            self.audit.execution(
                "agent.execution.completed",
                execution_id=execution_id,
                agent_id=agent_id,
                workflow_id=workflow_id,
                status=result["status"],
                actor=requested_by,
                metadata={
                    "artifacts_count": len(result["artifacts"]),
                    "duration_ms": self._duration_ms(started_at),
                },
            )
        if result["status"] == "blocked":
            self.audit.execution(
                "agent.execution.blocked",
                execution_id=execution_id,
                agent_id=agent_id,
                workflow_id=workflow_id,
                status=result["status"],
                actor=requested_by,
                severity="warning",
                metadata={"duration_ms": self._duration_ms(started_at)},
            )
        if result["status"] == "needs_structured_output_review":
            self.audit.execution(
                "agent.execution.needs_structured_output_review",
                execution_id=execution_id,
                agent_id=agent_id,
                workflow_id=workflow_id,
                status=result["status"],
                actor=requested_by,
                severity="warning",
                metadata={
                    "error_type": self._structured_error_value(
                        structured_output_error,
                        "type",
                    ),
                    "skill_id": self._structured_error_value(
                        structured_output_error,
                        "skill_id",
                    ),
                    "duration_ms": self._duration_ms(started_at),
                },
            )
        if workflow_execution["status"] == "paused_for_approval":
            self.audit.execution(
                "agent.execution.paused_for_approval",
                execution_id=execution_id,
                agent_id=agent_id,
                workflow_id=workflow_id,
                status=result["status"],
                actor=requested_by,
                metadata={
                    "checkpoint": approval["checkpoint"],
                    "duration_ms": self._duration_ms(started_at),
                },
            )
        result["persistence_path"] = str(path.relative_to(self.root))
        self._save_idempotency_record(
            key=idempotency_key,
            fingerprint=request_fingerprint,
            execution_id=execution_id,
        )
        return result

    def resume(self, execution_id: str) -> dict[str, Any]:
        started_at = perf_counter()
        execution = self.repo.load("executions", execution_id)
        if execution.get("status") == "completed":
            return execution
        if execution.get("status") != "approved_pending_resume":
            msg = f"{execution_id}: ejecucion no esta aprobada para reanudar"
            raise RequestValidationError(msg)
        approval = execution.get("approval", {})
        if not isinstance(approval, dict) or approval.get("status") != "approved":
            msg = f"{execution_id}: approval no aprobado"
            raise RequestValidationError(msg)
        checkpoint = approval.get("checkpoint")
        if not isinstance(checkpoint, str) or not checkpoint:
            msg = f"{execution_id}: checkpoint de approval invalido"
            raise RequestValidationError(msg)

        agent_id = self._required_execution_value(execution, "agent_id")
        workflow_id = self._required_execution_value(execution, "workflow_id")
        requested_by = self._required_execution_value(execution, "requested_by")
        business_pack_value = execution.get("business_pack_id")
        business_pack_id = business_pack_value if isinstance(business_pack_value, str) else None
        request_input = execution.get("input", {})
        if not isinstance(request_input, dict):
            request_input = {}
        composed_context = execution.get("composed_context", {})
        if not isinstance(composed_context, dict):
            composed_context = {}

        self.audit.execution(
            "agent.execution.resume.started",
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            status="started",
            actor=requested_by,
            metadata={"checkpoint": checkpoint},
        )
        resumed_workflow_execution = WorkflowEngine(
            self.root,
            business_pack_id=business_pack_id,
            skill_executor=self._skill_executor(
                business_pack_id=business_pack_id,
                composed_context=composed_context,
                execution_id=execution_id,
            ),
            composed_context=composed_context,
            correlation_id=execution_id,
        ).run(
            agent_id=agent_id,
            workflow_id=workflow_id,
            request_input=request_input,
            resume_after_checkpoint=checkpoint,
        )

        previous_workflow_execution = execution.get("workflow_execution", {})
        if not isinstance(previous_workflow_execution, dict):
            previous_workflow_execution = {}
        combined_workflow_execution = self._combine_resumed_workflow_execution(
            previous=previous_workflow_execution,
            resumed=resumed_workflow_execution,
            approval=approval,
        )
        execution["workflow_execution"] = combined_workflow_execution
        execution["evaluation"] = EvaluationEngine(
            self.root,
            business_pack_id=business_pack_id,
            model_gateway=self.evaluation_model_gateway,
        ).evaluate_workflow(
            agent_id=agent_id,
            workflow_id=workflow_id,
            workflow_execution=combined_workflow_execution,
            correlation_id=execution_id,
        )
        execution["structured_output_error"] = combined_workflow_execution.get(
            "structured_output_error"
        )
        execution["status"] = self._execution_status(combined_workflow_execution)
        new_artifacts = self._create_artifacts(
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            workflow_execution=resumed_workflow_execution,
            approval=approval,
        )
        existing_artifacts = execution.get("artifacts", [])
        if not isinstance(existing_artifacts, list):
            existing_artifacts = []
        execution["artifacts"] = [*existing_artifacts, *new_artifacts]
        path = self.repo.save("executions", execution_id, execution)
        self.audit.execution(
            "agent.execution.resumed",
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            status=str(execution["status"]),
            actor=requested_by,
            metadata={
                "checkpoint": checkpoint,
                "artifacts_count": len(new_artifacts),
                "persistence_path": str(path.relative_to(self.root)),
                "duration_ms": self._duration_ms(started_at),
            },
        )
        return execution

    def _skill_executor(
        self,
        *,
        business_pack_id: str | None,
        composed_context: dict[str, Any],
        execution_id: str,
    ) -> SkillExecutor | None:
        if not self.execute_skills:
            return None
        model_gateway = self.model_gateway
        if model_gateway is None:
            model_gateway = ModelGateway(
                adapter=create_model_adapter(root=self.root),
                root=self.root,
            )
        return SkillExecutor(
            self.root,
            business_pack_id=business_pack_id,
            model_gateway=model_gateway,
        )

    def _find_idempotent_execution(
        self,
        *,
        key: str,
        fingerprint: str,
        agent_id: str,
        workflow_id: str,
        actor: str,
    ) -> dict[str, Any] | None:
        storage_id = idempotency_storage_id(key)
        if not self.repo.exists("idempotency", storage_id):
            return None
        record = self.repo.load("idempotency", storage_id)
        stored_fingerprint = record.get("fingerprint")
        execution_id = record.get("execution_id")
        if stored_fingerprint != fingerprint:
            self.audit.error(
                "idempotency.conflict",
                error_type="IdempotencyConflictError",
                message="idempotency key usada con request distinto",
                actor=actor,
                metadata={"agent_id": agent_id, "workflow_id": workflow_id},
            )
            msg = "idempotency_key ya fue usada con otro request"
            raise IdempotencyConflictError(msg)
        if not isinstance(execution_id, str) or not execution_id:
            msg = "registro de idempotencia invalido"
            raise TypeError(msg)
        execution = self.repo.load("executions", execution_id)
        self.audit.execution(
            "agent.execution.idempotency_replayed",
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            status=str(execution.get("status", "unknown")),
            actor=actor,
            metadata={"idempotency_key": key},
        )
        return replay_execution(execution=execution, key=key)

    def _save_idempotency_record(
        self,
        *,
        key: str,
        fingerprint: str,
        execution_id: str,
    ) -> None:
        self.repo.save(
            "idempotency",
            idempotency_storage_id(key),
            {
                "key": key,
                "fingerprint": fingerprint,
                "execution_id": execution_id,
            },
        )

    def _execution_status(self, workflow_execution: dict[str, Any]) -> str:
        if workflow_execution["status"] == "paused_for_approval":
            return "pending_human_approval"
        if workflow_execution["status"] == "needs_structured_output_review":
            return "needs_structured_output_review"
        if workflow_execution["status"] == "blocked":
            return "blocked"
        return "completed"

    def _combine_resumed_workflow_execution(
        self,
        *,
        previous: dict[str, Any],
        resumed: dict[str, Any],
        approval: dict[str, Any],
    ) -> dict[str, Any]:
        previous_steps = previous.get("steps", [])
        if not isinstance(previous_steps, list):
            previous_steps = []
        resumed_steps = resumed.get("steps", [])
        if not isinstance(resumed_steps, list):
            resumed_steps = []
        errors = [
            *self._list_value(previous.get("errors")),
            *self._list_value(resumed.get("errors")),
        ]
        return {
            **previous,
            "status": resumed.get("status", "completed"),
            "steps": [
                *self._mark_approval_step_approved(previous_steps, approval),
                *resumed_steps,
            ],
            "errors": errors,
            "approval": {
                **approval,
                "required": True,
            },
            "structured_output_error": resumed.get("structured_output_error"),
            "resumed_after_checkpoint": approval.get("checkpoint"),
        }

    def _mark_approval_step_approved(
        self,
        steps: list[dict[str, Any]],
        approval: dict[str, Any],
    ) -> list[dict[str, Any]]:
        checkpoint = approval.get("checkpoint")
        updated_steps: list[dict[str, Any]] = []
        for step in steps:
            updated = dict(step)
            if (
                updated.get("type") == "approval"
                and updated.get("checkpoint") == checkpoint
            ):
                updated["status"] = "approved"
                updated["decision"] = approval.get("decision")
                updated["approval_id"] = approval.get("approval_id")
            updated_steps.append(updated)
        return updated_steps

    def _required_execution_value(self, execution: dict[str, Any], key: str) -> str:
        value = execution.get(key)
        if not isinstance(value, str) or not value:
            msg = f"{key} requerido en ejecucion"
            raise RequestValidationError(msg)
        return value

    def _validate_run_request(self, request: dict[str, Any]) -> None:
        if not isinstance(request, dict):
            msg = "request debe ser objeto"
            raise RequestValidationError(msg)
        required = ("agent_id", "workflow_id", "requested_by")
        missing = [field for field in required if not isinstance(request.get(field), str)]
        if missing:
            msg = f"request invalido; campos requeridos string: {missing}"
            raise RequestValidationError(msg)
        request_input = request.get("input", {})
        if not isinstance(request_input, dict):
            msg = "input debe ser objeto"
            raise RequestValidationError(msg)

    def _list_value(self, value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    def _structured_error_value(
        self,
        structured_output_error: Any,
        key: str,
    ) -> str | None:
        if isinstance(structured_output_error, dict):
            value = structured_output_error.get(key)
            return value if isinstance(value, str) else None
        return None

    def _duration_ms(self, started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1000))

    def _create_artifacts(
        self,
        *,
        execution_id: str,
        agent_id: str,
        workflow_id: str,
        workflow_execution: dict[str, Any],
        approval: dict[str, Any],
    ) -> list[dict[str, Any]]:
        manager = ArtifactManager(self.root)
        artifacts = []
        for action in self._reached_actions(workflow_execution.get("steps", [])):
            artifact_type = ACTION_ARTIFACT_TYPES.get(action)
            if artifact_type is None:
                continue
            status = "pending_approval" if approval.get("status") == "pending" else "draft"
            artifacts.append(
                manager.create(
                    execution_id=execution_id,
                    agent_id=agent_id,
                    workflow_id=workflow_id,
                    artifact_type=artifact_type,
                    source_action=action,
                    status=status,
                    metadata={
                        "approval_id": approval.get("approval_id"),
                        "checkpoint": approval.get("checkpoint"),
                        "requires_approval": approval.get("required", False),
                    },
                )
            )
        return artifacts

    def _reached_actions(self, steps: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        for step in steps:
            if step.get("status") == "skipped":
                continue
            if step.get("type") == "action" and isinstance(step.get("action"), str):
                actions.append(step["action"])
            for child_key in ("branches", "steps"):
                children = step.get(child_key)
                if isinstance(children, list):
                    actions.extend(self._reached_actions(children))
            nested = step.get("step")
            if isinstance(nested, dict):
                actions.extend(self._reached_actions([nested]))
        return actions
