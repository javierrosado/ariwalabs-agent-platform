from pathlib import Path
from textwrap import dedent

from ariwalabs.handoff_registry import HandoffRegistry


def test_handoff_registry_accepts_repository_handoffs() -> None:
    root = Path(__file__).resolve().parents[2]
    findings = HandoffRegistry(root).validate_repository()

    assert findings == []


def test_handoff_registry_blocks_unknown_producer(tmp_path: Path) -> None:
    write_handoff_fixture(tmp_path, producer="unknown-agent")

    findings = HandoffRegistry(tmp_path).validate_repository()

    assert any("producer desconocido" in finding["message"] for finding in findings)


def test_handoff_registry_blocks_sensitive_handoff_without_approval(tmp_path: Path) -> None:
    write_handoff_fixture(tmp_path, approval_required=False)

    findings = HandoffRegistry(tmp_path).validate_repository()

    assert any("requiere aprobacion humana" in finding["message"] for finding in findings)


def test_handoff_registry_blocks_sqlite_persistence(tmp_path: Path) -> None:
    write_handoff_fixture(tmp_path, persistence_current="sqlite")

    findings = HandoffRegistry(tmp_path).validate_repository()

    assert any("no usar SQLite" in finding["message"] for finding in findings)


def test_handoff_registry_blocks_missing_errors(tmp_path: Path) -> None:
    write_handoff_fixture(tmp_path, errors=[])

    findings = HandoffRegistry(tmp_path).validate_repository()

    assert any("errors vacio" in finding["message"] for finding in findings)


def test_handoff_registry_blocks_missing_idempotency(tmp_path: Path) -> None:
    write_handoff_fixture(tmp_path, idempotency_key_strategy="")

    findings = HandoffRegistry(tmp_path).validate_repository()

    assert any("idempotency.key_strategy vacio" in finding["message"] for finding in findings)


def write_handoff_fixture(
    root: Path,
    *,
    producer: str = "sample-agent",
    approval_required: bool = True,
    persistence_current: str = "runtime/data",
    errors: list[str] | None = None,
    idempotency_key_strategy: str = "execution_id",
) -> None:
    agent_dir = root / "agents" / "sample-agent"
    handoffs_dir = root / "docs" / "handoffs"
    agent_dir.mkdir(parents=True)
    handoffs_dir.mkdir(parents=True)
    (agent_dir / "agent.yaml").write_text(
        dedent(
            """
            agent:
              id: sample-agent
              name: Sample Agent
              version: 0.1.0
              purpose: Validate handoff registry behavior.
              owner: company-director
              autonomy: supervised
              skills: []
              workflows: []
            """
        ).strip(),
        encoding="utf-8",
    )
    errors = ["missing_approval"] if errors is None else errors
    errors_yaml = format_yaml_list(errors, indent=18)
    (handoffs_dir / "sample-handoffs.yaml").write_text(
        dedent(
            f"""
            handoffs:
              - id: sample-to-director
                version: 0.1.0
                producer: {producer}
                consumer: company-director
                trigger: campaign_release
                input:
                  required:
                    - request
                output:
                  required:
                    - approval_request
                preconditions:
                  - explicit_director_review
                approval:
                  required: {str(approval_required).lower()}
                  approver: company-director
                  checkpoint: approve_campaign
                persistence:
                  current: {persistence_current}
                  future: Airtable
                errors:
{errors_yaml}
                idempotency:
                  key_strategy: "{idempotency_key_strategy}"
            """
        ).strip(),
        encoding="utf-8",
    )


def format_yaml_list(values: list[str], *, indent: int) -> str:
    padding = " " * indent
    if not values:
        return f"{padding}[]"
    return "\n".join(f"{padding}- {value}" for value in values)
