import json
import sys
from pathlib import Path

from ariwalabs.approval_engine import ApprovalEngine
from ariwalabs.cli import main
from ariwalabs.repository import JsonRepository


def test_approval_cli_lists_pending_approvals(tmp_path: Path, capsys) -> None:
    approval = create_pending_approval(tmp_path)

    exit_code = run_cli(
        "ariwalabs",
        "approval",
        "list",
        "--root",
        str(tmp_path),
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output[0]["approval_id"] == approval["approval_id"]


def test_approval_cli_approves_with_reason(tmp_path: Path, capsys) -> None:
    approval = create_pending_approval(tmp_path)

    exit_code = run_cli(
        "ariwalabs",
        "approval",
        "decide",
        approval["approval_id"],
        "--decision",
        "approved",
        "--reason",
        "Revisado por Javier.",
        "--root",
        str(tmp_path),
    )
    output = json.loads(capsys.readouterr().out)
    execution = JsonRepository(tmp_path / "runtime/data").load("executions", "exec-test")

    assert exit_code == 0
    assert output["status"] == "approved"
    assert execution["status"] == "approved_pending_resume"


def test_approval_cli_rejects_with_reason(tmp_path: Path, capsys) -> None:
    approval = create_pending_approval(tmp_path)

    exit_code = run_cli(
        "ariwalabs",
        "approval",
        "decide",
        approval["approval_id"],
        "--decision",
        "rejected",
        "--reason",
        "Falta evidencia.",
        "--root",
        str(tmp_path),
    )
    output = json.loads(capsys.readouterr().out)
    execution = JsonRepository(tmp_path / "runtime/data").load("executions", "exec-test")

    assert exit_code == 0
    assert output["status"] == "rejected"
    assert execution["status"] == "rejected"


def test_approval_cli_requires_reason(tmp_path: Path) -> None:
    approval = create_pending_approval(tmp_path)

    try:
        run_cli(
            "ariwalabs",
            "approval",
            "decide",
            approval["approval_id"],
            "--decision",
            "approved",
            "--root",
            str(tmp_path),
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("CLI sin --reason debio fallar")


def test_approval_cli_rejects_invalid_decision(tmp_path: Path) -> None:
    approval = create_pending_approval(tmp_path)

    try:
        run_cli(
            "ariwalabs",
            "approval",
            "decide",
            approval["approval_id"],
            "--decision",
            "maybe",
            "--reason",
            "Intento invalido.",
            "--root",
            str(tmp_path),
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("CLI con decision invalida debio fallar")


def test_execution_cli_resumes_approved_execution(
    tmp_path: Path,
    capsys,
) -> None:
    root = Path(__file__).resolve().parents[2]
    execution = JsonRepository(root / "runtime/data").load(
        "executions",
        create_resume_fixture(root),
    )
    execution_id = execution["execution_id"]

    exit_code = run_cli(
        "ariwalabs",
        "execution",
        "resume",
        execution_id,
        "--root",
        str(root),
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["execution_id"] == execution_id
    assert output["status"] == "completed"


def create_pending_approval(root: Path) -> dict[str, object]:
    repo = JsonRepository(root / "runtime/data")
    repo.save("executions", "exec-test", {"execution_id": "exec-test", "approval": {}})
    return ApprovalEngine(root).create_pending(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        checkpoint="approve_campaign",
        approver="company-director",
    )


def run_cli(*args: str) -> int:
    original_argv = sys.argv
    sys.argv = list(args)
    try:
        return main()
    finally:
        sys.argv = original_argv


def create_resume_fixture(root: Path) -> str:
    from uuid import uuid4

    from ariwalabs.runtime import AgentRuntime

    runtime = AgentRuntime(root, execute_skills=False)
    key = f"test-cli-resume-{uuid4().hex}"
    result = runtime.run(
        {
            "agent_id": "growth-marketing-agent",
            "workflow_id": "create-training-campaign",
            "requested_by": "company-director",
            "idempotency_key": key,
            "input": {"objective": f"CLI resume {key}"},
        }
    )
    ApprovalEngine(root).decide(
        approval_id=result["approval"]["approval_id"],
        decision="approved",
        reason="Aprobado desde test CLI.",
        decided_by="company-director",
    )
    return str(result["execution_id"])
