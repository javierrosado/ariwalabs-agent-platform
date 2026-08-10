from pathlib import Path

from ariwalabs.approval_engine import ApprovalEngine
from ariwalabs.repository import JsonRepository


def test_approval_engine_creates_and_lists_pending_approval(tmp_path: Path) -> None:
    approval = ApprovalEngine(tmp_path).create_pending(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        checkpoint="approve_campaign",
        approver="company-director",
    )

    pending = ApprovalEngine(tmp_path).list_pending()

    assert approval["status"] == "pending"
    assert pending == [approval]


def test_approval_engine_approves_and_updates_execution(tmp_path: Path) -> None:
    repo = JsonRepository(tmp_path / "runtime/data")
    repo.save("executions", "exec-test", {"execution_id": "exec-test", "approval": {}})
    engine = ApprovalEngine(tmp_path)
    approval = engine.create_pending(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        checkpoint="approve_campaign",
        approver="company-director",
    )

    decided = engine.decide(
        approval_id=approval["approval_id"],
        decision="approved",
        reason="Contenido revisado por Javier.",
        decided_by="company-director",
    )
    execution = repo.load("executions", "exec-test")

    assert decided["status"] == "approved"
    assert engine.list_pending() == []
    assert execution["status"] == "approved_pending_resume"
    assert execution["approval"]["approval_id"] == approval["approval_id"]


def test_approval_engine_rejects_and_updates_execution(tmp_path: Path) -> None:
    repo = JsonRepository(tmp_path / "runtime/data")
    repo.save("executions", "exec-test", {"execution_id": "exec-test", "approval": {}})
    engine = ApprovalEngine(tmp_path)
    approval = engine.create_pending(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        checkpoint="approve_campaign",
        approver="company-director",
    )

    engine.decide(
        approval_id=approval["approval_id"],
        decision="rejected",
        reason="Falta evidencia.",
        decided_by="company-director",
    )
    execution = repo.load("executions", "exec-test")

    assert execution["status"] == "rejected"
    assert execution["approval"]["decision"] == "rejected"


def test_approval_engine_blocks_decision_without_reason(tmp_path: Path) -> None:
    repo = JsonRepository(tmp_path / "runtime/data")
    repo.save("executions", "exec-test", {"execution_id": "exec-test", "approval": {}})
    engine = ApprovalEngine(tmp_path)
    approval = engine.create_pending(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        checkpoint="approve_campaign",
        approver="company-director",
    )

    try:
        engine.decide(
            approval_id=approval["approval_id"],
            decision="approved",
            reason="",
            decided_by="company-director",
        )
    except ValueError as exc:
        assert "reason es obligatorio" in str(exc)
    else:
        raise AssertionError("decision sin reason debio fallar")


def test_approval_engine_blocks_double_decision(tmp_path: Path) -> None:
    repo = JsonRepository(tmp_path / "runtime/data")
    repo.save("executions", "exec-test", {"execution_id": "exec-test", "approval": {}})
    engine = ApprovalEngine(tmp_path)
    approval = engine.create_pending(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        checkpoint="approve_campaign",
        approver="company-director",
    )
    engine.decide(
        approval_id=approval["approval_id"],
        decision="approved",
        reason="Aprobado.",
        decided_by="company-director",
    )

    try:
        engine.decide(
            approval_id=approval["approval_id"],
            decision="rejected",
            reason="Cambio de opinion.",
            decided_by="company-director",
        )
    except ValueError as exc:
        assert "approval ya decidido" in str(exc)
    else:
        raise AssertionError("doble decision debio fallar")


def test_approval_engine_blocks_non_director_decision(tmp_path: Path) -> None:
    engine = ApprovalEngine(tmp_path)

    try:
        engine.decide(
            approval_id="appr-test",
            decision="approved",
            reason="Aprobado.",
            decided_by="other-user",
        )
    except ValueError as exc:
        assert "decided_by debe ser company-director" in str(exc)
    else:
        raise AssertionError("decision de otro usuario debio fallar")
