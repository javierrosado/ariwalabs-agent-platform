from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .audit import AuditLogger
from .repository import JsonRepository

VALID_STATUSES = {
    "approved",
    "archived",
    "draft",
    "pending_approval",
    "rejected",
}


class ArtifactManager:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.repo = JsonRepository(self.root / "runtime/data")
        self.audit = AuditLogger(self.root / "runtime/data/audit.jsonl")

    def create(
        self,
        *,
        execution_id: str,
        agent_id: str,
        workflow_id: str,
        artifact_type: str,
        source_action: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._validate_required(
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            artifact_type=artifact_type,
            source_action=source_action,
        )
        if status not in VALID_STATUSES:
            msg = f"status invalido {status}"
            raise ValueError(msg)

        artifact_id = f"art-{uuid4().hex[:12]}"
        artifact = {
            "artifact_id": artifact_id,
            "execution_id": execution_id,
            "agent_id": agent_id,
            "workflow_id": workflow_id,
            "artifact_type": artifact_type,
            "source_action": source_action,
            "status": status,
            "metadata": metadata or {},
            "version": "0.1.0",
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.repo.save("artifacts", artifact_id, artifact)
        self.audit.artifact(
            "artifact.created",
            artifact_id=artifact_id,
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            artifact_type=artifact_type,
            source_action=source_action,
            status=status,
        )
        return artifact

    def list_all(self) -> list[dict[str, Any]]:
        return [self.repo.load("artifacts", path.stem) for path in self.repo.list("artifacts")]

    def list_by_execution(self, execution_id: str) -> list[dict[str, Any]]:
        return [
            artifact
            for artifact in self.list_all()
            if artifact.get("execution_id") == execution_id
        ]

    def _validate_required(
        self,
        *,
        execution_id: str,
        agent_id: str,
        workflow_id: str,
        artifact_type: str,
        source_action: str,
    ) -> None:
        values = {
            "execution_id": execution_id,
            "agent_id": agent_id,
            "workflow_id": workflow_id,
            "artifact_type": artifact_type,
            "source_action": source_action,
        }
        missing = [field for field, value in values.items() if not value.strip()]
        if missing:
            msg = f"campos requeridos vacios: {missing}"
            raise ValueError(msg)
