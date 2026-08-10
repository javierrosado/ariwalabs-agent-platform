import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

VALID_SEVERITIES = {"debug", "info", "warning", "error", "critical"}
SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "client_secret",
    "password",
    "secret",
    "token",
}
MAX_PAYLOAD_DEPTH = 6
MAX_STRING_LENGTH = 500
REDACTED = "[REDACTED]"


class AuditLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        severity: str = "info",
        actor: str = "system",
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        if not event_type.strip():
            msg = "event_type es obligatorio"
            raise ValueError(msg)
        if severity not in VALID_SEVERITIES:
            msg = f"severity invalido {severity}"
            raise ValueError(msg)
        event = {
            "event_id": f"evt-{uuid4().hex[:12]}",
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "severity": severity,
            "actor": actor,
            "correlation_id": correlation_id,
            "payload": self._sanitize(payload),
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def execution(
        self,
        event_type: str,
        *,
        execution_id: str,
        agent_id: str,
        workflow_id: str,
        status: str,
        actor: str = "system",
        severity: str = "info",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.append(
            event_type,
            {
                "execution_id": execution_id,
                "agent_id": agent_id,
                "workflow_id": workflow_id,
                "status": status,
                "metadata": metadata or {},
            },
            severity=severity,
            actor=actor,
            correlation_id=execution_id,
        )

    def validation(
        self,
        event_type: str,
        *,
        target: str,
        status: str,
        findings_count: int,
        errors_count: int,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.append(
            event_type,
            {
                "target": target,
                "status": status,
                "findings_count": findings_count,
                "errors_count": errors_count,
                "metadata": metadata or {},
            },
            severity="error" if errors_count else "info",
            correlation_id=target,
        )

    def approval(
        self,
        event_type: str,
        *,
        approval_id: str,
        execution_id: str,
        agent_id: str,
        workflow_id: str,
        checkpoint: str,
        status: str,
        actor: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.append(
            event_type,
            {
                "approval_id": approval_id,
                "execution_id": execution_id,
                "agent_id": agent_id,
                "workflow_id": workflow_id,
                "checkpoint": checkpoint,
                "status": status,
                "metadata": metadata or {},
            },
            actor=actor,
            correlation_id=execution_id,
        )

    def artifact(
        self,
        event_type: str,
        *,
        artifact_id: str,
        execution_id: str,
        agent_id: str,
        workflow_id: str,
        artifact_type: str,
        source_action: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.append(
            event_type,
            {
                "artifact_id": artifact_id,
                "execution_id": execution_id,
                "agent_id": agent_id,
                "workflow_id": workflow_id,
                "artifact_type": artifact_type,
                "source_action": source_action,
                "status": status,
                "metadata": metadata or {},
            },
            correlation_id=execution_id,
        )

    def error(
        self,
        event_type: str,
        *,
        error_type: str,
        message: str,
        actor: str = "system",
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.append(
            event_type,
            {
                "error_type": error_type,
                "message": message,
                "metadata": metadata or {},
            },
            severity="error",
            actor=actor,
            correlation_id=correlation_id,
        )

    def cost(
        self,
        event_type: str,
        *,
        execution_id: str,
        logical_profile: str,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        estimated_cost: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.append(
            event_type,
            {
                "execution_id": execution_id,
                "logical_profile": logical_profile,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "estimated_cost": estimated_cost,
                "metadata": metadata or {},
            },
            correlation_id=execution_id,
        )

    def _sanitize(self, value: Any, depth: int = 0) -> Any:
        if depth > MAX_PAYLOAD_DEPTH:
            return "[MAX_DEPTH]"
        if isinstance(value, dict):
            sanitized: dict[str, Any] = {}
            for key, item in value.items():
                safe_key = str(key)
                if self._is_sensitive_key(safe_key):
                    sanitized[safe_key] = REDACTED
                else:
                    sanitized[safe_key] = self._sanitize(item, depth + 1)
            return sanitized
        if isinstance(value, list):
            return [self._sanitize(item, depth + 1) for item in value]
        if isinstance(value, tuple):
            return [self._sanitize(item, depth + 1) for item in value]
        if isinstance(value, str):
            return value[:MAX_STRING_LENGTH]
        return value

    def _is_sensitive_key(self, key: str) -> bool:
        normalized = key.lower().replace("-", "_")
        return normalized in SENSITIVE_KEYS or normalized.endswith("_token")
