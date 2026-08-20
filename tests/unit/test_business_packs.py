from pathlib import Path
from textwrap import dedent

from ariwalabs.business_packs import BusinessPackRegistry
from ariwalabs.framework_validator import FrameworkValidator


def test_business_pack_registry_validates_repository_packs() -> None:
    root = Path(__file__).resolve().parents[2]

    findings = BusinessPackRegistry(root).validate_repository()

    assert findings == []


def test_business_pack_resolves_ariwalabs_agent_path() -> None:
    root = Path(__file__).resolve().parents[2]

    agent_path = BusinessPackRegistry(root).agent_path(
        "growth-marketing-agent",
        "ariwalabs-training",
    )

    assert (
        agent_path
        == root
        / "business_packs"
        / "ariwalabs-training"
        / "agents"
        / "growth-marketing-agent"
    )


def test_framework_validator_accepts_example_service_pack() -> None:
    root = Path(__file__).resolve().parents[2]

    result = FrameworkValidator(
        root,
        business_pack_id="example-service",
    ).validate_repository()

    assert result["status"] == "passed", result


def test_framework_validator_accepts_business_pack() -> None:
    root = Path(__file__).resolve().parents[2]

    result = FrameworkValidator(
        root,
        business_pack_id="ariwalabs-training",
    ).validate_repository()

    assert result["status"] == "passed", result


def test_business_pack_registry_reports_missing_assets(tmp_path: Path) -> None:
    pack_dir = tmp_path / "business_packs" / "sample-pack"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.yaml").write_text(
        dedent(
            """
            business_pack:
              id: sample-pack
              name: Sample Pack
              version: 0.1.0
              owner: company-director
              purpose: Sample.
              domain_assets:
                agents:
                  - agents/missing-agent
                context: []
                policies: []
                handoffs: []
            """
        ).strip(),
        encoding="utf-8",
    )

    findings = BusinessPackRegistry(tmp_path).validate_repository()

    assert findings == [
        {
            "severity": "error",
            "message": (
                "business_packs/sample-pack/pack.yaml: "
                "ruta inexistente agents/missing-agent"
            ),
        }
    ]
