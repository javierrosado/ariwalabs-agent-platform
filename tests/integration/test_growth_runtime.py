from pathlib import Path
from uuid import uuid4

from ariwalabs.approval_engine import ApprovalEngine
from ariwalabs.artifact_manager import ArtifactManager
from ariwalabs.errors import AgentNotFoundError, RequestValidationError, WorkflowNotFoundError
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


def test_runtime_raises_typed_error_for_invalid_request() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)

    try:
        runtime.run({"agent_id": "growth-marketing-agent"})
    except RequestValidationError as exc:
        assert "campos requeridos" in str(exc)
    else:
        raise AssertionError("request invalido debio fallar")


def test_runtime_raises_typed_error_for_unknown_agent() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)

    try:
        runtime.run(
            {
                "agent_id": "unknown-agent",
                "workflow_id": "create-training-campaign",
                "requested_by": "company-director",
                "input": {},
            }
        )
    except AgentNotFoundError as exc:
        assert "agente inexistente" in str(exc)
    else:
        raise AssertionError("agente desconocido debio fallar")


def test_runtime_raises_typed_error_for_unknown_workflow() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)

    try:
        runtime.run(
            {
                "agent_id": "growth-marketing-agent",
                "workflow_id": "unknown-workflow",
                "requested_by": "company-director",
                "input": {},
            }
        )
    except WorkflowNotFoundError as exc:
        assert "workflow inexistente" in str(exc)
    else:
        raise AssertionError("workflow desconocido debio fallar")


def test_growth_runtime_persists_composed_context() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    result = runtime.run(
        {
            "agent_id": "growth-marketing-agent",
            "workflow_id": "manage-student-growth-journey",
            "requested_by": "company-director",
            "input": {"objective": "Context composition"},
        }
    )

    composed_context = result["composed_context"]
    assert composed_context["workflow_id"] == "manage-student-growth-journey"
    assert "shared/context/company-profile.yaml" in composed_context["source_paths"]
    assert composed_context["data"]["company"]["company"]["name"] == "AriwaLabs"


def test_growth_runtime_persists_independent_evaluation() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    key = f"test-evaluation-{uuid4().hex}"
    result = runtime.run(
        {
            "agent_id": "growth-marketing-agent",
            "workflow_id": "manage-student-growth-journey",
            "requested_by": "company-director",
            "idempotency_key": key,
            "input": {"objective": f"Independent evaluation {key}"},
        }
    )

    evaluation = result["evaluation"]
    assert evaluation["workflow_id"] == "manage-student-growth-journey"
    assert evaluation["status"] in {"passed", "passed_with_warnings"}
    assert evaluation["skill_evaluations"][0]["skill_id"] == (
        "growth-marketing.student-journey"
    )
    assert evaluation["skill_evaluations"][0]["status"] in {"passed", "passed_with_warnings"}


def test_growth_runtime_persists_real_skill_model_result() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    key = f"test-real-skill-{uuid4().hex}"
    result = runtime.run(
        {
            "agent_id": "growth-marketing-agent",
            "workflow_id": "manage-student-growth-journey",
            "requested_by": "company-director",
            "idempotency_key": key,
            "input": {"objective": f"Real skill execution {key}"},
        }
    )

    first_step = result["workflow_execution"]["steps"][0]
    assert first_step["status"] == "completed"
    assert first_step["model_result"]["profile"] == "reasoning"
    assert first_step["model_result"]["content"]["summary"] == "fake model response"


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


def test_runtime_resumes_campaign_after_approval_without_duplicate_approval() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root, execute_skills=False)
    key = f"test-resume-{uuid4().hex}"
    result = runtime.run(
        {
            "agent_id": "growth-marketing-agent",
            "workflow_id": "create-training-campaign",
            "requested_by": "company-director",
            "idempotency_key": key,
            "input": {"objective": f"Resume campaign {key}"},
        }
    )
    approval_id = result["approval"]["approval_id"]

    ApprovalEngine(root).decide(
        approval_id=approval_id,
        decision="approved",
        reason="Aprobado para continuar.",
        decided_by="company-director",
    )
    resumed = runtime.resume(result["execution_id"])
    artifacts = ArtifactManager(root).list_by_execution(result["execution_id"])

    assert resumed["status"] == "completed"
    assert resumed["workflow_execution"]["status"] == "completed"
    assert resumed["workflow_execution"]["steps"][5]["status"] == "approved"
    assert resumed["workflow_execution"]["steps"][6]["type"] == "action"
    assert resumed["workflow_execution"]["steps"][6]["action"] == "persist_artifacts"
    assert len(artifacts) == 1
    assert artifacts[0]["artifact_type"] == "workflow_artifacts"
    assert not any(
        approval["approval_id"] == approval_id for approval in ApprovalEngine(root).list_pending()
    )


def test_runtime_resume_rejects_unapproved_execution() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root, execute_skills=False)
    key = f"test-resume-reject-{uuid4().hex}"
    result = runtime.run(
        {
            "agent_id": "growth-marketing-agent",
            "workflow_id": "create-training-campaign",
            "requested_by": "company-director",
            "idempotency_key": key,
            "input": {"objective": f"Resume reject {key}"},
        }
    )

    try:
        runtime.resume(result["execution_id"])
    except ValueError as exc:
        assert "no esta aprobada para reanudar" in str(exc)
    else:
        raise AssertionError("resume sin aprobacion debio fallar")
