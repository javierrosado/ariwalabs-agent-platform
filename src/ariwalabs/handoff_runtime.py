import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from .audit import AuditLogger
from .errors import (
    HandoffApprovalRequiredError,
    HandoffNotFoundError,
    RequestValidationError,
)
from .handoff_registry import HandoffRecord, HandoffRegistry
from .repository import JsonRepository


@dataclass(frozen=True)
class HandoffExecutionRequest:
    handoff_id: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    actor: str = "system"
    correlation_id: str | None = None
    approved: bool = False
    approval_id: str | None = None
    idempotency_key: str | None = None


class HandoffRuntime:
    def __init__(self, root: Path, *, business_pack_id: str | None = None):
        self.root = root.resolve()
        self.business_pack_id = business_pack_id
        self.registry = HandoffRegistry(self.root, business_pack_id=business_pack_id)
        self.repo = JsonRepository(self.root / "runtime/data")
        self.audit = AuditLogger(self.root / "runtime/data/audit.jsonl")

    def execute(self, request: HandoffExecutionRequest) -> dict[str, Any]:
        started_at = perf_counter()
        record = self._handoff(request.handoff_id)
        self._validate_payloads(record, request)
        if record.approval_required and not request.approved:
            self.audit.append(
                "handoff.execution.blocked",
                {
                    "handoff_id": record.handoff_id,
                    "producer": record.producer,
                    "consumer": record.consumer,
                    "reason": "approval_required",
                    "checkpoint": record.approval_checkpoint,
                },
                severity="warning",
                actor=request.actor,
                correlation_id=request.correlation_id,
            )
            raise HandoffApprovalRequiredError(
                f"{record.handoff_id}: requiere aprobacion humana"
            )

        storage_key = request.idempotency_key or self._default_idempotency_key(
            record,
            request,
        )
        storage_id = self._storage_id(storage_key)
        if self.repo.exists("handoffs", storage_id):
            handoff = self.repo.load("handoffs", storage_id)
            handoff["idempotency"] = {
                **self._dict_or_empty(handoff.get("idempotency")),
                "replayed": True,
            }
            return handoff

        handoff_id = f"hnd-{uuid4().hex[:12]}"
        duration_ms = self._duration_ms(started_at)
        handoff = {
            "handoff_execution_id": handoff_id,
            "handoff_id": record.handoff_id,
            "handoff_version": record.version,
            "business_pack_id": self.business_pack_id,
            "producer": record.producer,
            "consumer": record.consumer,
            "trigger": record.trigger,
            "status": "created",
            "created_at": datetime.now(UTC).isoformat(),
            "approval": {
                "required": record.approval_required,
                "approver": record.approval_approver,
                "checkpoint": record.approval_checkpoint,
                "approved": request.approved,
                "approval_id": request.approval_id,
            },
            "input": request.input_payload,
            "output": request.output_payload,
            "contract": {
                **asdict(record),
                "path": str(record.path.relative_to(self.root)),
            },
            "idempotency": {
                "key": storage_key,
                "storage_id": storage_id,
                "strategy": record.idempotency_key_strategy,
                "replayed": False,
            },
            "duration_ms": duration_ms,
        }
        self.repo.save("handoffs", storage_id, handoff)
        self.audit.append(
            "handoff.execution.created",
            {
                "handoff_execution_id": handoff_id,
                "handoff_id": record.handoff_id,
                "producer": record.producer,
                "consumer": record.consumer,
                "approval_required": record.approval_required,
                "duration_ms": duration_ms,
            },
            actor=request.actor,
            correlation_id=request.correlation_id,
        )
        return handoff

    def _handoff(self, handoff_id: str) -> HandoffRecord:
        try:
            return self.registry.get_handoff(handoff_id)
        except KeyError as exc:
            raise HandoffNotFoundError(str(exc)) from exc

    def _validate_payloads(
        self,
        record: HandoffRecord,
        request: HandoffExecutionRequest,
    ) -> None:
        if not isinstance(request.input_payload, dict):
            msg = "input_payload debe ser objeto"
            raise RequestValidationError(msg)
        if not isinstance(request.output_payload, dict):
            msg = "output_payload debe ser objeto"
            raise RequestValidationError(msg)
        input_missing = [
            field for field in record.input_required if field not in request.input_payload
        ]
        output_missing = [
            field for field in record.output_required if field not in request.output_payload
        ]
        if input_missing or output_missing:
            msg = (
                f"{record.handoff_id}: payload incompleto "
                f"input_missing={input_missing} output_missing={output_missing}"
            )
            raise RequestValidationError(msg)

    def _default_idempotency_key(
        self,
        record: HandoffRecord,
        request: HandoffExecutionRequest,
    ) -> str:
        payload = {
            "handoff_id": record.handoff_id,
            "strategy": record.idempotency_key_strategy,
            "correlation_id": request.correlation_id,
            "input": request.input_payload,
            "output": request.output_payload,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"handoff-{hashlib.sha256(encoded).hexdigest()[:24]}"

    def _storage_id(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _dict_or_empty(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _duration_ms(self, started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1000))
