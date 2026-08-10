import json
from pathlib import Path

from ariwalabs.audit import AuditLogger


def test_audit_logger_writes_canonical_jsonl_event(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "runtime/data/audit.jsonl")

    event = logger.append(
        "agent.execution.created",
        {"execution_id": "exec-test"},
        actor="company-director",
        correlation_id="exec-test",
    )

    stored = json.loads((tmp_path / "runtime/data/audit.jsonl").read_text())
    assert event == stored
    assert stored["event_id"].startswith("evt-")
    assert stored["event_type"] == "agent.execution.created"
    assert stored["severity"] == "info"
    assert stored["actor"] == "company-director"
    assert stored["correlation_id"] == "exec-test"
    assert stored["payload"] == {"execution_id": "exec-test"}


def test_audit_logger_redacts_sensitive_payload_keys(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")

    event = logger.append(
        "adapter.request.error",
        {
            "api_key": "should-not-leak",
            "nested": {
                "access_token": "should-not-leak",
                "safe": "visible",
            },
        },
    )

    assert event["payload"]["api_key"] == "[REDACTED]"
    assert event["payload"]["nested"]["access_token"] == "[REDACTED]"
    assert event["payload"]["nested"]["safe"] == "visible"


def test_audit_logger_blocks_invalid_severity(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")

    try:
        logger.append("agent.execution.created", {}, severity="invalid")
    except ValueError as exc:
        assert "severity invalido" in str(exc)
    else:
        raise AssertionError("severity invalido debio fallar")


def test_audit_logger_writes_cost_event_without_provider_coupling(
    tmp_path: Path,
) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")

    event = logger.cost(
        "model.cost.recorded",
        execution_id="exec-test",
        logical_profile="reasoning",
        tokens_in=100,
        tokens_out=50,
        estimated_cost={"currency": "USD", "amount": 0.01},
    )

    assert event["correlation_id"] == "exec-test"
    assert event["payload"]["logical_profile"] == "reasoning"
    assert event["payload"]["tokens_in"] == 100
    assert event["payload"]["estimated_cost"]["currency"] == "USD"
