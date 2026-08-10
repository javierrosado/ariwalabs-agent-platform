import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any


class IdempotencyConflictError(ValueError):
    """La misma llave de idempotencia fue usada con otro request."""


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    fingerprint: str
    execution_id: str


def idempotency_key_for_request(request: dict[str, Any]) -> str:
    explicit_key = request.get("idempotency_key")
    if isinstance(explicit_key, str) and explicit_key.strip():
        return explicit_key.strip()
    fingerprint = fingerprint_request(request)
    return f"auto-{fingerprint[:24]}"


def idempotency_storage_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def fingerprint_request(request: dict[str, Any]) -> str:
    canonical_request = {
        "agent_id": request.get("agent_id"),
        "workflow_id": request.get("workflow_id"),
        "requested_by": request.get("requested_by"),
        "input": request.get("input", {}),
    }
    encoded = json.dumps(
        canonical_request,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def replay_execution(
    *,
    execution: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    replayed = copy.deepcopy(execution)
    stored_idempotency = replayed.get("idempotency")
    idempotency = stored_idempotency if isinstance(stored_idempotency, dict) else {}
    replayed["idempotency"] = {
        **idempotency,
        "key": key,
        "replayed": True,
        "original_execution_id": replayed.get("execution_id"),
    }
    return replayed
