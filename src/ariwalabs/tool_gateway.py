from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol
from uuid import uuid4

from .artifact_manager import ArtifactManager
from .audit import AuditLogger
from .errors import (
    RequestValidationError,
    ToolApprovalRequiredError,
    ToolExecutionError,
    ToolGatewayError,
    ToolNotFoundError,
)

Finding = dict[str, str]


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    category: str
    external: bool
    adapter: str | None = None
    allowed_in_skills: bool = True
    requires_approval: bool = False
    input_contract: tuple[str, ...] = ()
    output_contract: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolResolution:
    allowed: tuple[ToolDefinition, ...]
    prohibited: tuple[ToolDefinition, ...]


@dataclass(frozen=True)
class ToolExecutionRequest:
    tool_id: str
    payload: dict[str, Any]
    actor: str = "system"
    correlation_id: str | None = None
    approved: bool = False


@dataclass(frozen=True)
class ToolExecutionResult:
    tool_id: str
    status: str
    output: dict[str, Any]
    external: bool
    adapter: str | None
    duration_ms: int


class AirtableToolAdapter(Protocol):
    def list_records(self, table: str, **filters: Any) -> list[dict[str, Any]]:
        ...

    def create_draft(
        self,
        table: str,
        fields: dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        ...


TOOL_CATALOG: dict[str, ToolDefinition] = {
    "airtable-read": ToolDefinition(
        tool_id="airtable-read",
        category="operational-data",
        external=True,
        adapter="airtable",
        input_contract=("table",),
        output_contract=("records",),
    ),
    "airtable-write-draft": ToolDefinition(
        tool_id="airtable-write-draft",
        category="operational-data",
        external=True,
        adapter="airtable",
        requires_approval=True,
        input_contract=("table", "fields"),
        output_contract=("record",),
    ),
    "artifact-create": ToolDefinition(
        tool_id="artifact-create",
        category="framework",
        external=False,
        input_contract=(
            "execution_id",
            "agent_id",
            "workflow_id",
            "artifact_type",
            "source_action",
            "status",
        ),
        output_contract=("artifact",),
    ),
    "audit-append": ToolDefinition(
        tool_id="audit-append",
        category="framework",
        external=False,
        input_contract=("event_type", "payload"),
        output_contract=("event",),
    ),
    "external-publish": ToolDefinition(
        tool_id="external-publish",
        category="external-action",
        external=True,
        allowed_in_skills=False,
        requires_approval=True,
    ),
    "external-message": ToolDefinition(
        tool_id="external-message",
        category="external-action",
        external=True,
        allowed_in_skills=False,
        requires_approval=True,
    ),
    "payment": ToolDefinition(
        tool_id="payment",
        category="external-action",
        external=True,
        allowed_in_skills=False,
        requires_approval=True,
    ),
}


class ToolGateway:
    def __init__(
        self,
        root: Path,
        catalog: dict[str, ToolDefinition] | None = None,
        adapters: dict[str, Any] | None = None,
    ):
        self.root = root.resolve()
        self.catalog = catalog or TOOL_CATALOG
        self.adapters = adapters or {}
        self.audit = AuditLogger(self.root / "runtime/data/audit.jsonl")

    def resolve(
        self,
        *,
        allowed: tuple[str, ...],
        prohibited: tuple[str, ...],
    ) -> ToolResolution:
        return ToolResolution(
            allowed=tuple(self.catalog[tool_id] for tool_id in allowed if tool_id in self.catalog),
            prohibited=tuple(
                self.catalog[tool_id] for tool_id in prohibited if tool_id in self.catalog
            ),
        )

    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        started_at = perf_counter()
        definition = self.catalog.get(request.tool_id)
        if definition is None:
            raise ToolNotFoundError(f"tool desconocida {request.tool_id}")
        self._validate_payload(definition, request.payload)
        if definition.requires_approval and not request.approved:
            self.audit.append(
                "tool.execution.blocked",
                {
                    "tool_id": definition.tool_id,
                    "category": definition.category,
                    "external": definition.external,
                    "adapter": definition.adapter,
                    "reason": "approval_required",
                },
                severity="warning",
                actor=request.actor,
                correlation_id=request.correlation_id,
            )
            raise ToolApprovalRequiredError(
                f"{definition.tool_id}: requiere aprobacion humana"
            )
        tool_request_id = f"tool-{uuid4().hex[:12]}"
        self.audit.append(
            "tool.execution.started",
            {
                "tool_request_id": tool_request_id,
                "tool_id": definition.tool_id,
                "category": definition.category,
                "external": definition.external,
                "adapter": definition.adapter,
                "payload_keys": sorted(request.payload),
            },
            actor=request.actor,
            correlation_id=request.correlation_id,
        )
        try:
            output = self._dispatch(definition, request)
        except ToolGatewayError:
            raise
        except Exception as exc:
            duration_ms = self._duration_ms(started_at)
            self.audit.error(
                "tool.execution.failed",
                error_type=exc.__class__.__name__,
                message=str(exc),
                actor=request.actor,
                correlation_id=request.correlation_id,
                metadata={"tool_id": definition.tool_id, "duration_ms": duration_ms},
            )
            raise ToolExecutionError(f"{definition.tool_id}: fallo ejecucion") from exc
        duration_ms = self._duration_ms(started_at)
        self.audit.append(
            "tool.execution.completed",
            {
                "tool_request_id": tool_request_id,
                "tool_id": definition.tool_id,
                "category": definition.category,
                "external": definition.external,
                "adapter": definition.adapter,
                "output_keys": sorted(output),
                "duration_ms": duration_ms,
            },
            actor=request.actor,
            correlation_id=request.correlation_id,
        )
        return ToolExecutionResult(
            tool_id=definition.tool_id,
            status="completed",
            output=output,
            external=definition.external,
            adapter=definition.adapter,
            duration_ms=duration_ms,
        )

    def validate_skill_tools(
        self,
        *,
        skill_path: Path,
        allowed: tuple[str, ...],
        prohibited: tuple[str, ...],
    ) -> list[Finding]:
        findings: list[Finding] = []

        overlap = sorted(set(allowed) & set(prohibited))
        if overlap:
            findings.append(
                self._finding(
                    "error",
                    self._format(
                        skill_path,
                        f"tools simultaneamente permitidas y prohibidas: {overlap}",
                    ),
                )
            )

        unknown_allowed = self._unknown_tools(allowed)
        if unknown_allowed:
            findings.append(
                self._finding(
                    "error",
                    self._format(skill_path, f"tools allowed desconocidas: {unknown_allowed}"),
                )
            )

        unknown_prohibited = self._unknown_tools(prohibited)
        if unknown_prohibited:
            findings.append(
                self._finding(
                    "error",
                    self._format(
                        skill_path,
                        f"tools prohibited desconocidas: {unknown_prohibited}",
                    ),
                )
            )

        forbidden_allowed = sorted(
            {
                tool_id
                for tool_id in allowed
                if tool_id in self.catalog and not self.catalog[tool_id].allowed_in_skills
            }
        )
        if forbidden_allowed:
            findings.append(
                self._finding(
                    "error",
                    self._format(skill_path, f"tools prohibidas en allowed: {forbidden_allowed}"),
                )
            )

        return findings

    def _dispatch(
        self,
        definition: ToolDefinition,
        request: ToolExecutionRequest,
    ) -> dict[str, Any]:
        if definition.tool_id == "audit-append":
            return {"event": self._append_audit(request)}
        if definition.tool_id == "artifact-create":
            return {"artifact": self._create_artifact(request.payload)}
        if definition.tool_id == "airtable-read":
            adapter = self._adapter("airtable")
            records = adapter.list_records(
                str(request.payload["table"]),
                **self._filters(request.payload),
            )
            return {"records": records}
        if definition.tool_id == "airtable-write-draft":
            adapter = self._adapter("airtable")
            idempotency_key = request.payload.get("idempotency_key")
            if idempotency_key is not None and not isinstance(idempotency_key, str):
                msg = "idempotency_key debe ser string"
                raise RequestValidationError(msg)
            record = adapter.create_draft(
                str(request.payload["table"]),
                self._dict_payload(request.payload["fields"], "fields"),
                idempotency_key=idempotency_key,
            )
            return {"record": record}
        msg = f"{definition.tool_id}: no tiene handler ejecutable"
        raise ToolExecutionError(msg)

    def _append_audit(self, request: ToolExecutionRequest) -> dict[str, Any]:
        payload = request.payload
        return self.audit.append(
            str(payload["event_type"]),
            self._dict_payload(payload["payload"], "payload"),
            severity=str(payload.get("severity", "info")),
            actor=request.actor,
            correlation_id=request.correlation_id,
        )

    def _create_artifact(self, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = payload.get("metadata")
        return ArtifactManager(self.root).create(
            execution_id=str(payload["execution_id"]),
            agent_id=str(payload["agent_id"]),
            workflow_id=str(payload["workflow_id"]),
            artifact_type=str(payload["artifact_type"]),
            source_action=str(payload["source_action"]),
            status=str(payload["status"]),
            metadata=self._dict_payload(metadata, "metadata") if metadata is not None else None,
        )

    def _adapter(self, adapter_id: str) -> Any:
        adapter = self.adapters.get(adapter_id)
        if adapter is None:
            msg = f"adapter no configurado {adapter_id}"
            raise ToolExecutionError(msg)
        return adapter

    def _filters(self, payload: dict[str, Any]) -> dict[str, Any]:
        filters = payload.get("filters", {})
        if filters is None:
            return {}
        return self._dict_payload(filters, "filters")

    def _dict_payload(self, value: Any, field: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            msg = f"{field} debe ser objeto"
            raise RequestValidationError(msg)
        return value

    def _validate_payload(
        self,
        definition: ToolDefinition,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(payload, dict):
            msg = "payload debe ser objeto"
            raise RequestValidationError(msg)
        missing = [field for field in definition.input_contract if field not in payload]
        if missing:
            msg = f"{definition.tool_id}: faltan campos requeridos {missing}"
            raise RequestValidationError(msg)

    def _unknown_tools(self, values: tuple[str, ...]) -> list[str]:
        return sorted({tool_id for tool_id in values if tool_id not in self.catalog})

    def _format(self, path: Path, message: str) -> str:
        return f"{path.relative_to(self.root)}: {message}"

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}

    def _duration_ms(self, started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1000))
