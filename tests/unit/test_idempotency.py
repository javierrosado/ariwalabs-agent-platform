from ariwalabs.idempotency import (
    fingerprint_request,
    idempotency_key_for_request,
    idempotency_storage_id,
    replay_execution,
)


def test_idempotency_key_uses_explicit_request_key() -> None:
    request = {
        "agent_id": "growth-marketing-agent",
        "workflow_id": "create-training-campaign",
        "requested_by": "company-director",
        "idempotency_key": "campaign/2026/001",
        "input": {"objective": "Test"},
    }

    assert idempotency_key_for_request(request) == "campaign/2026/001"
    assert "/" not in idempotency_storage_id("campaign/2026/001")


def test_idempotency_key_is_stable_for_equivalent_request_ordering() -> None:
    first = {
        "agent_id": "growth-marketing-agent",
        "workflow_id": "create-training-campaign",
        "requested_by": "company-director",
        "input": {"objective": "Test", "budget": {"maximum": 1000, "currency": "PEN"}},
    }
    second = {
        "requested_by": "company-director",
        "workflow_id": "create-training-campaign",
        "agent_id": "growth-marketing-agent",
        "input": {"budget": {"currency": "PEN", "maximum": 1000}, "objective": "Test"},
    }

    assert fingerprint_request(first) == fingerprint_request(second)
    assert idempotency_key_for_request(first) == idempotency_key_for_request(second)


def test_replay_execution_marks_returned_payload_without_mutating_original() -> None:
    execution = {
        "execution_id": "exec-test",
        "idempotency": {"key": "sample", "fingerprint": "abc", "replayed": False},
    }

    replayed = replay_execution(execution=execution, key="sample")

    assert replayed["idempotency"]["replayed"] is True
    assert replayed["idempotency"]["original_execution_id"] == "exec-test"
    assert execution["idempotency"]["replayed"] is False
