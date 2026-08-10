from pathlib import Path
from uuid import uuid4

from ariwalabs.approval_engine import ApprovalEngine
from ariwalabs.artifact_manager import ArtifactManager
from ariwalabs.idempotency import IdempotencyConflictError
from ariwalabs.runtime import AgentRuntime


def test_growth_campaign_creates_execution() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    result = runtime.run(
        {
            "agent_id": "growth-marketing-agent",
            "workflow_id": "create-training-campaign",
            "requested_by": "company-director",
            "input": {"objective": "Test campaign"},
        }
    )
    assert result["status"] == "pending_human_approval"
    assert result["agent_id"] == "growth-marketing-agent"
    assert result["workflow_execution"]["status"] == "paused_for_approval"
    assert result["approval"]["checkpoint"] == "approve_campaign"
    assert result["approval"]["approval_id"].startswith("appr-")

    pending = ApprovalEngine(root).list_pending()
    assert any(
        approval["approval_id"] == result["approval"]["approval_id"]
        for approval in pending
    )
    assert result["artifacts"] == []


def test_student_journey_creates_state_artifact() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    result = runtime.run(
        {
            "agent_id": "growth-marketing-agent",
            "workflow_id": "manage-student-growth-journey",
            "requested_by": "company-director",
            "input": {"objective": "Test journey"},
        }
    )

    assert result["status"] == "completed"
    assert result["artifacts"][0]["artifact_type"] == "journey_state"

    artifacts = ArtifactManager(root).list_by_execution(result["execution_id"])
    assert artifacts[0]["artifact_id"] == result["artifacts"][0]["artifact_id"]


def test_growth_campaign_persists_structured_output_review_state() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    result = runtime.run(
        {
            "agent_id": "growth-marketing-agent",
            "workflow_id": "create-training-campaign",
            "requested_by": "company-director",
            "input": {
                "objective": "Test campaign",
                "__skill_results__": {
                    "growth-marketing.request-validation": {
                        "status": "invalid_output",
                        "profile": "fast_structured",
                        "provider": "openai",
                        "model": "gpt-test",
                        "error": {
                            "type": "ModelOutputError",
                            "message": "schema mismatch",
                            "retryable": True,
                        },
                    },
                },
            },
        }
    )

    assert result["status"] == "needs_structured_output_review"
    assert result["approval"]["required"] is False
    assert result["artifacts"] == []
    assert result["structured_output_error"]["skill_id"] == (
        "growth-marketing.request-validation"
    )


def test_runtime_idempotency_replays_campaign_without_duplicate_approval() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    key = f"test-campaign-{uuid4().hex}"
    request = {
        "agent_id": "growth-marketing-agent",
        "workflow_id": "create-training-campaign",
        "requested_by": "company-director",
        "idempotency_key": key,
        "input": {"objective": f"Idempotent campaign {key}"},
    }
    approvals_before = len(ApprovalEngine(root).list_pending())

    first = runtime.run(request)
    second = runtime.run(request)

    approvals_after = len(ApprovalEngine(root).list_pending())
    assert first["execution_id"] == second["execution_id"]
    assert first["idempotency"]["replayed"] is False
    assert second["idempotency"]["replayed"] is True
    assert second["idempotency"]["original_execution_id"] == first["execution_id"]
    assert approvals_after == approvals_before + 1


def test_runtime_idempotency_replays_journey_without_duplicate_artifact() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    key = f"test-journey-{uuid4().hex}"
    request = {
        "agent_id": "growth-marketing-agent",
        "workflow_id": "manage-student-growth-journey",
        "requested_by": "company-director",
        "idempotency_key": key,
        "input": {
            "objective": f"Idempotent journey {key}",
            "eligible_for_referral": True,
        },
    }

    first = runtime.run(request)
    second = runtime.run(request)
    artifacts = ArtifactManager(root).list_by_execution(first["execution_id"])

    assert first["execution_id"] == second["execution_id"]
    assert second["idempotency"]["replayed"] is True
    assert [artifact["artifact_type"] for artifact in artifacts] == ["journey_state"]


def test_runtime_idempotency_rejects_same_key_for_different_request() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    key = f"test-conflict-{uuid4().hex}"
    first_request = {
        "agent_id": "growth-marketing-agent",
        "workflow_id": "manage-student-growth-journey",
        "requested_by": "company-director",
        "idempotency_key": key,
        "input": {"objective": "First request"},
    }
    second_request = {
        **first_request,
        "input": {"objective": "Different request"},
    }

    runtime.run(first_request)
    try:
        runtime.run(second_request)
    except IdempotencyConflictError as exc:
        assert "idempotency_key ya fue usada" in str(exc)
    else:
        raise AssertionError("idempotency_key reutilizada debio fallar")
