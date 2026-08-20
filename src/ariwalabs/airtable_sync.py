from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from adapters.airtable.base import AirtableRecord

from .audit import AuditLogger
from .repository import JsonRepository


class AirtableSyncAdapter(Protocol):
    def create_draft(
        self,
        table: str,
        fields: dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> AirtableRecord:
        ...


@dataclass(frozen=True)
class AirtableSyncResult:
    execution_id: str
    records: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "synced",
            "execution_id": self.execution_id,
            "records_count": len(self.records),
            "records": self.records,
        }


class AirtableSync:
    def __init__(self, root: Path, *, adapter: AirtableSyncAdapter):
        self.root = root.resolve()
        self.adapter = adapter
        self.repo = JsonRepository(self.root / "runtime/data")
        self.audit = AuditLogger(self.root / "runtime/data/audit.jsonl")

    def sync_execution(self, execution_id: str) -> dict[str, Any]:
        execution = self.repo.load("executions", execution_id)
        records: list[dict[str, Any]] = []
        records.append(
            self._sync_record(
                table="AgentExecutions",
                entity_id=execution_id,
                fields=self._execution_fields(execution),
            )
        )
        approval = self._approval_payload(execution)
        if approval is not None:
            approval_id = str(approval["approval_id"])
            records.append(
                self._sync_record(
                    table="Approvals",
                    entity_id=approval_id,
                    fields=self._approval_fields(approval),
                )
            )
        for artifact in self._artifacts_for_execution(execution):
            artifact_id = str(artifact["artifact_id"])
            records.append(
                self._sync_record(
                    table="Artifacts",
                    entity_id=artifact_id,
                    fields=self._artifact_fields(artifact),
                )
            )
        result = AirtableSyncResult(execution_id=execution_id, records=tuple(records)).to_dict()
        self.audit.append(
            "airtable.sync.execution.completed",
            {
                "execution_id": execution_id,
                "records_count": result["records_count"],
                "tables": sorted({record["table"] for record in records}),
            },
            correlation_id=execution_id,
        )
        return result

    def _sync_record(
        self,
        *,
        table: str,
        entity_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        idempotency_key = f"{table}:{entity_id}"
        record = self.adapter.create_draft(
            table,
            fields,
            idempotency_key=idempotency_key,
        )
        record_id = record.get("id")
        return {
            "table": table,
            "entity_id": entity_id,
            "airtable_record_id": record_id if isinstance(record_id, str) else None,
            "idempotency_key": idempotency_key,
        }

    def _execution_fields(self, execution: dict[str, Any]) -> dict[str, Any]:
        workflow_execution = execution.get("workflow_execution", {})
        workflow_status = (
            workflow_execution.get("status")
            if isinstance(workflow_execution, dict)
            else "unknown"
        )
        return {
            "ExecutionId": self._required_str(execution, "execution_id"),
            "AgentId": self._required_str(execution, "agent_id"),
            "AgentVersion": self._required_str(execution, "agent_version"),
            "WorkflowId": self._required_str(execution, "workflow_id"),
            "RequestedBy": self._required_str(execution, "requested_by"),
            "Status": self._required_str(execution, "status"),
            "WorkflowStatus": str(workflow_status),
            "CreatedAt": self._required_str(execution, "created_at"),
        }

    def _approval_fields(self, approval: dict[str, Any]) -> dict[str, Any]:
        fields = {
            "ApprovalId": self._required_str(approval, "approval_id"),
            "ExecutionId": self._required_str(approval, "execution_id"),
            "AgentId": self._required_str(approval, "agent_id"),
            "WorkflowId": self._required_str(approval, "workflow_id"),
            "Checkpoint": self._required_str(approval, "checkpoint"),
            "Approver": self._required_str(approval, "approver"),
            "Status": self._required_str(approval, "status"),
            "CreatedAt": self._required_str(approval, "created_at"),
        }
        self._copy_optional(approval, fields, "decision", "Decision")
        self._copy_optional(approval, fields, "decided_by", "DecidedBy")
        self._copy_optional(approval, fields, "decided_at", "DecidedAt")
        self._copy_optional(approval, fields, "reason", "Reason")
        return fields

    def _artifact_fields(self, artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "ArtifactId": self._required_str(artifact, "artifact_id"),
            "ExecutionId": self._required_str(artifact, "execution_id"),
            "AgentId": self._required_str(artifact, "agent_id"),
            "WorkflowId": self._required_str(artifact, "workflow_id"),
            "ArtifactType": self._required_str(artifact, "artifact_type"),
            "SourceAction": self._required_str(artifact, "source_action"),
            "Status": self._required_str(artifact, "status"),
            "Version": self._required_str(artifact, "version"),
            "CreatedAt": self._required_str(artifact, "created_at"),
        }

    def _approval_payload(self, execution: dict[str, Any]) -> dict[str, Any] | None:
        raw_approval = execution.get("approval")
        if not isinstance(raw_approval, dict):
            return None
        approval_id = raw_approval.get("approval_id")
        if not isinstance(approval_id, str) or not approval_id:
            return None
        if self.repo.exists("approvals", approval_id):
            return self.repo.load("approvals", approval_id)
        return {
            "approval_id": approval_id,
            "execution_id": execution.get("execution_id"),
            "agent_id": execution.get("agent_id"),
            "workflow_id": execution.get("workflow_id"),
            "checkpoint": raw_approval.get("checkpoint"),
            "approver": raw_approval.get("approver"),
            "status": raw_approval.get("status"),
            "created_at": execution.get("created_at"),
            "decision": raw_approval.get("decision"),
            "reason": raw_approval.get("reason"),
            "decided_by": raw_approval.get("decided_by"),
            "decided_at": raw_approval.get("decided_at"),
        }

    def _artifacts_for_execution(self, execution: dict[str, Any]) -> list[dict[str, Any]]:
        execution_id = self._required_str(execution, "execution_id")
        artifacts: list[dict[str, Any]] = []
        for raw_artifact in execution.get("artifacts", []):
            if isinstance(raw_artifact, dict):
                artifacts.append(raw_artifact)
        known_ids = {
            artifact.get("artifact_id")
            for artifact in artifacts
            if isinstance(artifact.get("artifact_id"), str)
        }
        for path in self.repo.list("artifacts"):
            artifact = self.repo.load("artifacts", path.stem)
            artifact_id = artifact.get("artifact_id")
            if artifact.get("execution_id") == execution_id and artifact_id not in known_ids:
                artifacts.append(artifact)
        return artifacts

    def _required_str(self, payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            msg = f"{key} requerido para sincronizacion Airtable"
            raise ValueError(msg)
        return value

    def _copy_optional(
        self,
        source: dict[str, Any],
        target: dict[str, Any],
        source_key: str,
        target_key: str,
    ) -> None:
        value = source.get(source_key)
        if isinstance(value, str) and value:
            target[target_key] = value
