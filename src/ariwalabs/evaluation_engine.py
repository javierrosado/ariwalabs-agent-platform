from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from adapters.models.base import ModelResult

from .audit import AuditLogger
from .business_packs import BusinessPackRegistry
from .config import load_yaml

Finding = dict[str, str]

EVALUATION_OUTPUT_SCHEMA: dict[str, Any] = {
    "title": "skill-evaluation",
    "type": "object",
    "required": ["status", "score", "findings", "recommendations", "errors"],
    "properties": {
        "status": {"type": "string", "enum": ["passed", "passed_with_warnings", "blocked"]},
        "score": {"type": "number"},
        "findings": {"type": "array", "items": {"type": "string"}},
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "errors": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


class EvaluationModelGateway(Protocol):
    def generate_structured(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
        correlation_id: str | None = None,
        skill_id: str | None = None,
    ) -> ModelResult:
        ...


@dataclass(frozen=True)
class RubricCriterion:
    criterion_id: str
    weight: float
    description: str
    required: bool


@dataclass(frozen=True)
class SkillRubric:
    skill_id: str
    version: str
    min_score: float
    criteria: tuple[RubricCriterion, ...]


class EvaluationEngine:
    def __init__(
        self,
        root: Path,
        *,
        business_pack_id: str | None = None,
        model_gateway: EvaluationModelGateway | None = None,
    ):
        self.root = root.resolve()
        self.business_pack_id = business_pack_id
        self.business_packs = BusinessPackRegistry(self.root)
        self.model_gateway = model_gateway
        self.audit = AuditLogger(self.root / "runtime/data/audit.jsonl")

    def validate_repository(self) -> list[Finding]:
        findings: list[Finding] = []
        agent_dirs = self.business_packs.agent_dirs(self.business_pack_id)
        if not agent_dirs:
            return findings
        for agent_dir in agent_dirs:
            config = load_yaml(agent_dir / "agent.yaml").get("agent", {})
            agent_id = str(config.get("id", agent_dir.name))
            skill_ids = self._agent_skill_ids(agent_dir)
            findings.extend(self.validate_agent_rubrics(agent_id=agent_id, skill_ids=skill_ids))
        return findings

    def validate_agent_rubrics(
        self,
        *,
        agent_id: str,
        skill_ids: set[str],
    ) -> list[Finding]:
        rubric_path = self._rubric_path(agent_id)
        if not rubric_path.exists():
            return [self._finding("error", f"{agent_id}: falta evaluations/rubrics.yaml")]
        payload = load_yaml(rubric_path).get("evaluation")
        if not isinstance(payload, dict):
            return [self._finding("error", f"{agent_id}: falta seccion evaluation")]

        findings: list[Finding] = []
        if payload.get("agent_id") != agent_id:
            findings.append(self._finding("error", f"{agent_id}: evaluation.agent_id invalido"))
        if not isinstance(payload.get("version"), str):
            findings.append(self._finding("error", f"{agent_id}: evaluation.version requerido"))

        rubrics = payload.get("rubrics")
        if not isinstance(rubrics, dict):
            return findings + [self._finding("error", f"{agent_id}: rubrics debe ser objeto")]

        rubric_ids = {key for key in rubrics if isinstance(key, str)}
        for skill_id in sorted(skill_ids - rubric_ids):
            findings.append(self._finding("error", f"{agent_id}: falta rubrica para {skill_id}"))
        for rubric_id in sorted(rubric_ids - skill_ids):
            findings.append(
                self._finding("error", f"{agent_id}: rubrica sin skill {rubric_id}")
            )
        for skill_id, raw_rubric in rubrics.items():
            if not isinstance(skill_id, str) or not isinstance(raw_rubric, dict):
                findings.append(self._finding("error", f"{agent_id}: rubrica invalida"))
                continue
            findings.extend(self._validate_rubric(agent_id, skill_id, raw_rubric))
        return findings

    def evaluate_workflow(
        self,
        *,
        agent_id: str,
        workflow_id: str,
        workflow_execution: dict[str, Any],
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        skill_steps = self._skill_steps(workflow_execution.get("steps", []))
        self.audit.append(
            "evaluation.workflow.started",
            {
                "agent_id": agent_id,
                "workflow_id": workflow_id,
                "skill_steps_count": len(skill_steps),
            },
            correlation_id=correlation_id,
        )
        evaluations = [
            self.evaluate_skill_step(
                agent_id=agent_id,
                workflow_id=workflow_id,
                step=step,
                correlation_id=correlation_id,
            )
            for step in skill_steps
        ]
        status = self._workflow_status(evaluations)
        self.audit.append(
            "evaluation.workflow.completed",
            {
                "agent_id": agent_id,
                "workflow_id": workflow_id,
                "status": status,
                "evaluations_count": len(evaluations),
            },
            correlation_id=correlation_id,
        )
        return {
            "status": status,
            "agent_id": agent_id,
            "workflow_id": workflow_id,
            "skill_evaluations": evaluations,
        }

    def evaluate_skill_step(
        self,
        *,
        agent_id: str,
        workflow_id: str,
        step: dict[str, Any],
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        skill_id = step["ref"]
        rubric = self._load_rubric(agent_id=agent_id, skill_id=skill_id)
        model_result = step.get("model_result")
        if not isinstance(model_result, dict) or not isinstance(model_result.get("content"), dict):
            return {
                "skill_id": skill_id,
                "status": "skipped_no_output",
                "score": None,
                "rubric_version": rubric.version,
                "criteria": [],
                "model_evaluation": {"status": "skipped"},
                "errors": [],
            }

        content = model_result["content"]
        schema = self._output_schema(agent_id=agent_id, skill_id=skill_id)
        criteria_results = [
            self._evaluate_criterion(criterion, content=content, schema=schema)
            for criterion in rubric.criteria
        ]
        score = self._score(criteria_results)
        status = self._skill_status(
            score=score,
            min_score=rubric.min_score,
            criteria=criteria_results,
        )
        model_evaluation = self._model_evaluation(
            agent_id=agent_id,
            workflow_id=workflow_id,
            skill_id=skill_id,
            content=content,
            rubric=rubric,
            correlation_id=correlation_id,
        )
        return {
            "skill_id": skill_id,
            "status": status,
            "score": score,
            "rubric_version": rubric.version,
            "criteria": criteria_results,
            "model_evaluation": model_evaluation,
            "errors": [item["message"] for item in criteria_results if item["status"] == "failed"],
        }

    def _validate_rubric(
        self,
        agent_id: str,
        skill_id: str,
        raw_rubric: dict[str, Any],
    ) -> list[Finding]:
        findings: list[Finding] = []
        min_score = raw_rubric.get("min_score")
        if not isinstance(min_score, (int, float)) or not 0 <= min_score <= 1:
            findings.append(
                self._finding("error", f"{agent_id}: {skill_id} min_score invalido")
            )
        criteria = raw_rubric.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            return findings + [
                self._finding("error", f"{agent_id}: {skill_id} criteria requerido")
            ]
        total_weight = 0.0
        for raw_criterion in criteria:
            if not isinstance(raw_criterion, dict):
                findings.append(
                    self._finding("error", f"{agent_id}: {skill_id} criterio invalido")
                )
                continue
            criterion_id = raw_criterion.get("id")
            weight = raw_criterion.get("weight")
            description = raw_criterion.get("description")
            if not isinstance(criterion_id, str) or not criterion_id:
                findings.append(
                    self._finding("error", f"{agent_id}: {skill_id} criterio sin id")
                )
            if not isinstance(weight, (int, float)) or weight <= 0:
                findings.append(
                    self._finding("error", f"{agent_id}: {skill_id} criterio weight invalido")
                )
            else:
                total_weight += float(weight)
            if not isinstance(description, str) or not description:
                findings.append(
                    self._finding("error", f"{agent_id}: {skill_id} criterio sin descripcion")
                )
        if total_weight > 1.0001:
            findings.append(
                self._finding("error", f"{agent_id}: {skill_id} suma de weights mayor a 1")
            )
        return findings

    def _evaluate_criterion(
        self,
        criterion: RubricCriterion,
        *,
        content: dict[str, Any],
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        if criterion.criterion_id == "schema_compliance":
            errors = sorted(
                error.message
                for error in Draft202012Validator(schema).iter_errors(content)
            )
            return self._criterion_result(
                criterion,
                passed=not errors,
                message="; ".join(errors),
            )
        if criterion.criterion_id == "no_declared_errors":
            declared_errors = content.get("errors")
            passed = not isinstance(declared_errors, list) or len(declared_errors) == 0
            return self._criterion_result(
                criterion,
                passed=passed,
                message="output declara errores",
            )
        if criterion.criterion_id == "approval_consistency":
            approval_required = content.get("approval_required")
            approval_reason = content.get("approval_reason")
            passed = approval_required is not True or isinstance(approval_reason, str)
            return self._criterion_result(
                criterion,
                passed=passed,
                message="approval_required requiere approval_reason",
            )
        if criterion.criterion_id == "policy_alignment":
            violations = content.get("violations")
            blocking = []
            if isinstance(violations, list):
                blocking = [
                    violation
                    for violation in violations
                    if isinstance(violation, dict) and violation.get("blocking") is True
                ]
            return self._criterion_result(
                criterion,
                passed=not blocking,
                message="output declara violaciones bloqueantes",
            )
        return self._criterion_result(criterion, passed=True, message="")

    def _criterion_result(
        self,
        criterion: RubricCriterion,
        *,
        passed: bool,
        message: str,
    ) -> dict[str, Any]:
        return {
            "id": criterion.criterion_id,
            "status": "passed" if passed else "failed",
            "weight": criterion.weight,
            "required": criterion.required,
            "message": "" if passed else message,
        }

    def _model_evaluation(
        self,
        *,
        agent_id: str,
        workflow_id: str,
        skill_id: str,
        content: dict[str, Any],
        rubric: SkillRubric,
        correlation_id: str | None,
    ) -> dict[str, Any]:
        if self.model_gateway is None:
            return {"status": "skipped"}
        result = self.model_gateway.generate_structured(
            profile="evaluation",
            system_prompt="Evalua el output de la skill contra su rubrica declarada.",
            payload={
                "agent_id": agent_id,
                "workflow_id": workflow_id,
                "skill_id": skill_id,
                "rubric": {
                    "min_score": rubric.min_score,
                    "criteria": [
                        {
                            "id": criterion.criterion_id,
                            "weight": criterion.weight,
                            "description": criterion.description,
                            "required": criterion.required,
                        }
                        for criterion in rubric.criteria
                    ],
                },
                "output": content,
            },
            output_schema=EVALUATION_OUTPUT_SCHEMA,
            correlation_id=correlation_id,
            skill_id=skill_id,
        )
        return {
            "status": result.get("status"),
            "profile": result.get("profile", "evaluation"),
            "content": result.get("content"),
            "error": result.get("error"),
        }

    def _skill_status(
        self,
        *,
        score: float,
        min_score: float,
        criteria: list[dict[str, Any]],
    ) -> str:
        if any(item["status"] == "failed" and item["required"] for item in criteria):
            return "blocked"
        if score < min_score:
            return "blocked"
        if any(item["status"] == "failed" for item in criteria):
            return "passed_with_warnings"
        return "passed"

    def _workflow_status(self, evaluations: list[dict[str, Any]]) -> str:
        statuses = [evaluation["status"] for evaluation in evaluations]
        if any(status == "blocked" for status in statuses):
            return "blocked"
        if any(status == "passed_with_warnings" for status in statuses):
            return "passed_with_warnings"
        if any(status == "passed" for status in statuses):
            return "passed"
        return "skipped_no_outputs"

    def _score(self, criteria: list[dict[str, Any]]) -> float:
        total_weight = sum(float(item["weight"]) for item in criteria)
        if total_weight == 0:
            return 0.0
        passed_weight = sum(
            float(item["weight"]) for item in criteria if item["status"] == "passed"
        )
        return round(passed_weight / total_weight, 4)

    def _load_rubric(self, *, agent_id: str, skill_id: str) -> SkillRubric:
        payload = load_yaml(self._rubric_path(agent_id)).get("evaluation", {})
        rubrics = payload.get("rubrics", {}) if isinstance(payload, dict) else {}
        raw_rubric = rubrics.get(skill_id, {}) if isinstance(rubrics, dict) else {}
        if not isinstance(raw_rubric, dict):
            raw_rubric = {}
        version = str(payload.get("version", "")) if isinstance(payload, dict) else ""
        criteria = tuple(
            RubricCriterion(
                criterion_id=str(raw_criterion["id"]),
                weight=float(raw_criterion["weight"]),
                description=str(raw_criterion["description"]),
                required=bool(raw_criterion.get("required", False)),
            )
            for raw_criterion in raw_rubric.get("criteria", [])
            if isinstance(raw_criterion, dict)
            and isinstance(raw_criterion.get("id"), str)
            and isinstance(raw_criterion.get("weight"), (int, float))
            and isinstance(raw_criterion.get("description"), str)
        )
        return SkillRubric(
            skill_id=skill_id,
            version=version,
            min_score=float(raw_rubric.get("min_score", 1.0)),
            criteria=criteria,
        )

    def _output_schema(self, *, agent_id: str, skill_id: str) -> dict[str, Any]:
        skill_path = self._skill_path(agent_id=agent_id, skill_id=skill_id)
        skill = load_yaml(skill_path).get("skill", {})
        output_schema = skill.get("output_schema")
        if not isinstance(output_schema, str):
            return {}
        return load_yaml((skill_path.parent / output_schema).resolve())

    def _skill_path(self, *, agent_id: str, skill_id: str) -> Path:
        agent_path = self.business_packs.agent_path(agent_id, self.business_pack_id)
        for skill_path in agent_path.glob("skills/*/skill.yaml"):
            skill = load_yaml(skill_path).get("skill", {})
            if skill.get("id") == skill_id:
                return skill_path
        msg = f"skill inexistente {skill_id}"
        raise ValueError(msg)

    def _skill_steps(self, steps: Any) -> list[dict[str, Any]]:
        if not isinstance(steps, list):
            return []
        found: list[dict[str, Any]] = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            if step.get("type") == "skill" and isinstance(step.get("ref"), str):
                found.append(step)
            nested = step.get("step")
            if isinstance(nested, dict):
                found.extend(self._skill_steps([nested]))
            for child_key in ("branches", "steps"):
                children = step.get(child_key)
                if isinstance(children, list):
                    found.extend(self._skill_steps(children))
        return found

    def _agent_skill_ids(self, agent_dir: Path) -> set[str]:
        skill_ids: set[str] = set()
        for skill_path in agent_dir.glob("skills/*/skill.yaml"):
            skill = load_yaml(skill_path).get("skill", {})
            skill_id = skill.get("id")
            if isinstance(skill_id, str):
                skill_ids.add(skill_id)
        return skill_ids

    def _rubric_path(self, agent_id: str) -> Path:
        return (
            self.business_packs.agent_path(agent_id, self.business_pack_id)
            / "evaluations"
            / "rubrics.yaml"
        )

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}
