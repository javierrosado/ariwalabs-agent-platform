from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .approval_engine import ApprovalEngine
from .artifact_manager import ArtifactManager
from .audit import AuditLogger
from .config import load_yaml
from .idempotency import (
    IdempotencyConflictError,
    fingerprint_request,
    idempotency_key_for_request,
    idempotency_storage_id,
    replay_execution,
)
from .repository import JsonRepository
from .workflow_engine import WorkflowEngine

ACTION_ARTIFACT_TYPES = {
    "consolidate_validation_report": "framework_validation_report",
    "persist_artifacts": "workflow_artifacts",
    "persist_draft_opportunity": "draft_opportunity",
    "persist_report": "growth_report",
    "persist_state": "journey_state",
}


class AgentRuntime:
    def __init__(self, root: Path):
        self.root = root
        self.repo = JsonRepository(root / "runtime/data")
        self.audit = AuditLogger(root / "runtime/data/audit.jsonl")

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        agent_id = request["agent_id"]
        agent_path = self.root / "agents" / agent_id
        config = load_yaml(agent_path / "agent.yaml")["agent"]
        workflow_id = request["workflow_id"]
        workflow = load_yaml(agent_path / "workflows" / f"{workflow_id}.yaml")
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
            workflow_execution = WorkflowEngine(self.root).run(
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
            "requested_by": requested_by,
            "created_at": datetime.now(UTC).isoformat(),
            "status": "pending_human_approval",
            "input": request.get("input", {}),
            "workflow_definition": workflow,
            "workflow_execution": workflow_execution,
            "shared_context": config.get("shared_context", []),
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
                metadata={"artifacts_count": len(result["artifacts"])},
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
                metadata={"checkpoint": approval["checkpoint"]},
            )
        result["persistence_path"] = str(path.relative_to(self.root))
        self._save_idempotency_record(
            key=idempotency_key,
            fingerprint=request_fingerprint,
            execution_id=execution_id,
        )
        return result

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

    def _structured_error_value(
        self,
        structured_output_error: Any,
        key: str,
    ) -> str | None:
        if isinstance(structured_output_error, dict):
            value = structured_output_error.get(key)
            return value if isinstance(value, str) else None
        return None

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
