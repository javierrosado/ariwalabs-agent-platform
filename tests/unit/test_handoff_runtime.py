import json
import sys
from pathlib import Path
from typing import Any

import pytest

from ariwalabs.cli import main
from ariwalabs.errors import HandoffApprovalRequiredError, RequestValidationError
from ariwalabs.handoff_runtime import HandoffExecutionRequest, HandoffRuntime
from ariwalabs.repository import JsonRepository


def test_handoff_runtime_blocks_when_approval_is_required() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = HandoffRuntime(root, business_pack_id="ariwalabs-training")

    with pytest.raises(HandoffApprovalRequiredError):
        runtime.execute(
            HandoffExecutionRequest(
                handoff_id="growth-marketing-to-director",
                input_payload=_director_input(),
                output_payload=_director_output(),
                correlation_id="exec-test",
            )
        )


def test_handoff_runtime_creates_idempotent_transition() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = HandoffRuntime(root, business_pack_id="ariwalabs-training")
    request = HandoffExecutionRequest(
        handoff_id="growth-marketing-to-director",
        input_payload=_director_input(),
        output_payload=_director_output(),
        actor="company-director",
        correlation_id="exec-test",
        approved=True,
        approval_id="appr-test",
        idempotency_key="handoff-runtime-test",
    )

    first = runtime.execute(request)
    second = runtime.execute(request)
    persisted = JsonRepository(root / "runtime/data").load(
        "handoffs",
        first["idempotency"]["storage_id"],
    )

    assert first["status"] == "created"
    assert first["approval"]["approved"] is True
    assert first["duration_ms"] >= 0
    assert second["handoff_execution_id"] == first["handoff_execution_id"]
    assert second["idempotency"]["replayed"] is True
    assert persisted["handoff_id"] == "growth-marketing-to-director"


def test_handoff_runtime_validates_required_payload_fields() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = HandoffRuntime(root, business_pack_id="ariwalabs-training")

    with pytest.raises(RequestValidationError):
        runtime.execute(
            HandoffExecutionRequest(
                handoff_id="growth-marketing-to-director",
                input_payload={"request": "missing fields"},
                output_payload=_director_output(),
                approved=True,
            )
        )


def test_handoff_cli_executes_approved_handoff(
    tmp_path: Path,
    capsys: Any,
) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(_director_input()), encoding="utf-8")
    output_file.write_text(json.dumps(_director_output()), encoding="utf-8")

    exit_code = run_cli(
        "ariwalabs",
        "handoff",
        "execute",
        "growth-marketing-to-director",
        "--root",
        str(Path(__file__).resolve().parents[2]),
        "--business-pack",
        "ariwalabs-training",
        "--input",
        str(input_file),
        "--output",
        str(output_file),
        "--approved",
        "--approval-id",
        "appr-cli",
        "--idempotency-key",
        "handoff-cli-test",
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["handoff_id"] == "growth-marketing-to-director"
    assert output["approval"]["approval_id"] == "appr-cli"


def _director_input() -> dict[str, Any]:
    return {
        "request": {"objective": "Campaign"},
        "shared_context_refs": ["company-profile"],
        "operational_data_refs": [],
        "restrictions": ["human_approval_required"],
    }


def _director_output() -> dict[str, Any]:
    return {
        "recommendation": {"summary": "Proceed as draft."},
        "artifacts": [],
        "risks": ["needs review"],
        "approval_request": {"checkpoint": "approve_commercial_action"},
    }


def run_cli(*args: str) -> int:
    original_argv = sys.argv
    sys.argv = list(args)
    try:
        return main()
    finally:
        sys.argv = original_argv
