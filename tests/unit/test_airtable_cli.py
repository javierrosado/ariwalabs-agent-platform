import json
import sys
from pathlib import Path

from ariwalabs.cli import main


def test_airtable_cli_returns_json_error_for_adapter_failure(
    tmp_path: Path,
    capsys,
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


def run_cli(*args: str) -> int:
    original_argv = sys.argv
    sys.argv = list(args)
    try:
        return main()
    finally:
        sys.argv = original_argv
