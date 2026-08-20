import json
import sys
from pathlib import Path
from typing import Any

from ariwalabs.cli import main
from ariwalabs.repository import JsonRepository


def test_airtable_cli_returns_json_error_for_adapter_failure(
    tmp_path: Path,
    capsys: Any,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("AIRTABLE_BASE_ID=app123\n", encoding="utf-8")

    exit_code = run_cli(
        "ariwalabs",
        "airtable",
        "validate-access",
        "--root",
        str(tmp_path),
        "--env-file",
        ".env",
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "failed"
    assert output["error_type"] == "AirtableConfigError"
    assert "AIRTABLE_TOKEN es obligatorio" in output["message"]


def test_airtable_cli_sync_execution_uses_airtable_sync(
    tmp_path: Path,
    capsys: Any,
    monkeypatch: Any,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("AIRTABLE_TOKEN=test-token\nAIRTABLE_BASE_ID=app123\n", encoding="utf-8")
    JsonRepository(tmp_path / "runtime/data").save(
        "executions",
        "exec-test",
        {
            "execution_id": "exec-test",
            "agent_id": "growth-marketing-agent",
            "agent_version": "0.2.0",
            "workflow_id": "create-training-campaign",
            "requested_by": "company-director",
            "created_at": "2026-08-15T00:00:00+00:00",
            "status": "completed",
            "workflow_execution": {"status": "completed"},
            "approval": {},
            "artifacts": [],
        },
    )

    from adapters.airtable import client

    monkeypatch.setattr(client, "AirtableHttpAdapter", FakeAirtableHttpAdapter)

    exit_code = run_cli(
        "ariwalabs",
        "airtable",
        "sync-execution",
        "exec-test",
        "--root",
        str(tmp_path),
        "--env-file",
        ".env",
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["status"] == "synced"
    assert output["records"][0]["table"] == "AgentExecutions"


def run_cli(*args: str) -> int:
    original_argv = sys.argv
    sys.argv = list(args)
    try:
        return main()
    finally:
        sys.argv = original_argv


class FakeAirtableHttpAdapter:
    def __init__(self, **kwargs: Any):
        self.kwargs = kwargs

    def validate_access(self, *, table: str | None = None) -> dict[str, Any]:
        return {"status": "passed", "table": table}

    def create_draft(
        self,
        table: str,
        fields: dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return {
            "id": f"rec-{table}",
            "fields": fields,
            "idempotency_key": idempotency_key,
        }
