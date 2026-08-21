from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .audit import AuditLogger
from .repository import JsonRepository
from .schema_validator import CoreSchemaValidator


class ApprovalEngine:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.repo = JsonRepository(self.root / "runtime/data")
        self.audit = AuditLogger(self.root / "runtime/data/audit.jsonl")
        self.schema_validator = CoreSchemaValidator(self.root)

    def create_pending(
        self,
        *,
        execution_id: str,
        agent_id: str,
        workflow_id: str,
        checkpoint: str,
        approver: str,
    ) -> dict[str, Any]:
        if approver != "company-director":
            msg = "approver debe ser company-director"
            raise ValueError(msg)
        approval_id = f"appr-{uuid4().hex[:12]}"
        approval = {
            "approval_id": approval_id,
            "execution_id": execution_id,
            "agent_id": agent_id,
            "workflow_id": workflow_id,
            "checkpoint": checkpoint,
            "approver": approver,
            "status": "pending",
            "created_at": datetime.now(UTC).isoformat(),
            "decided_at": None,
            "decision": None,
            "reason": None,
            "decided_by": None,
        }
        self._validate_approval_record(approval)
        self.repo.save("approvals", approval_id, approval)
        self.audit.approval(
            "approval.created",
            approval_id=approval_id,
            execution_id=execution_id,
            agent_id=agent_id,
            workflow_id=workflow_id,
            checkpoint=checkpoint,
            status="pending",
        )
        return approval

    def list_pending(self) -> list[dict[str, Any]]:
        approvals = []
        for path in self.repo.list("approvals"):
            approval = self.repo.load("approvals", path.stem)
            if approval.get("status") == "pending":
                approvals.append(approval)
        return approvals

    def decide(
        self,
        *,
        approval_id: str,
        decision: str,
        reason: str,
        decided_by: str,
    ) -> dict[str, Any]:
        if decision not in {"approved", "rejected"}:
            msg = "decision debe ser approved o rejected"
            raise ValueError(msg)
        if decided_by != "company-director":
            msg = "decided_by debe ser company-director"
            raise ValueError(msg)
        if not reason.strip():
            msg = "reason es obligatorio"
            raise ValueError(msg)

        approval = self.repo.load("approvals", approval_id)
        if approval.get("status") != "pending":
            msg = f"{approval_id}: approval ya decidido"
            raise ValueError(msg)

        approval["status"] = decision
        approval["decision"] = decision
        approval["reason"] = reason
        approval["decided_by"] = decided_by
        approval["decided_at"] = datetime.now(UTC).isoformat()
        self._validate_approval_record(approval)
        self.repo.save("approvals", approval_id, approval)
        self._update_execution(approval)
        self.audit.approval(
            f"approval.{decision}",
            approval_id=approval_id,
            execution_id=str(approval["execution_id"]),
            agent_id=str(approval["agent_id"]),
            workflow_id=str(approval["workflow_id"]),
            checkpoint=str(approval["checkpoint"]),
            status=decision,
            actor=decided_by,
            metadata={"decision": decision},
        )
        return approval

    def _update_execution(self, approval: dict[str, Any]) -> None:
        execution_id = str(approval["execution_id"])
        execution = self.repo.load("executions", execution_id)
        execution["approval"] = {
            **execution.get("approval", {}),
            "approval_id": approval["approval_id"],
            "status": approval["status"],
            "decision": approval["decision"],
            "reason": approval["reason"],
            "decided_by": approval["decided_by"],
            "decided_at": approval["decided_at"],
        }
        execution["status"] = (
            "approved_pending_resume"
            if approval["decision"] == "approved"
            else "rejected"
        )
        self.repo.save("executions", execution_id, execution)

    def _validate_approval_record(self, approval: dict[str, Any]) -> None:
        findings = self.schema_validator.validate_payload(
            payload=approval,
            schema_name="approval.schema.json",
            source_path=self.root / "runtime/data/approvals",
        )
        if findings:
            messages = "; ".join(finding["message"] for finding in findings)
            msg = f"approval invalido: {messages}"
            raise ValueError(msg)
