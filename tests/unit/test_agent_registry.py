from pathlib import Path
from textwrap import dedent

import pytest

from ariwalabs.agent_registry import AgentRegistry
from ariwalabs.framework_validator import FrameworkValidator


def test_agent_registry_lists_default_agents() -> None:
    root = Path(__file__).resolve().parents[2]

    agents = AgentRegistry(root).list_agents()

    agent_ids = {agent["agent_id"] for agent in agents}
    assert {"framework-agent", "growth-marketing-agent"} <= agent_ids


def test_agent_registry_lists_ariwalabs_pack_agents() -> None:
    root = Path(__file__).resolve().parents[2]

    agents = AgentRegistry(root, business_pack_id="ariwalabs-training").list_agents()

    growth_agent = next(agent for agent in agents if agent["agent_id"] == "growth-marketing-agent")
    assert growth_agent["business_pack_id"] == "ariwalabs-training"
    assert growth_agent["path"] == (
        "business_packs/ariwalabs-training/agents/growth-marketing-agent"
    )
    assert (
        "business_packs/ariwalabs-training/policies/ariwalabs-training-policy.yaml"
        in growth_agent["policies"]
    )


def test_agent_registry_lists_example_service_pack_agent() -> None:
    root = Path(__file__).resolve().parents[2]

    agents = AgentRegistry(root, business_pack_id="example-service").list_agents()

    assert [agent["agent_id"] for agent in agents] == ["service-ops-agent"]


def test_agent_registry_shows_agent() -> None:
    root = Path(__file__).resolve().parents[2]

    agent = AgentRegistry(root, business_pack_id="example-service").get_agent("service-ops-agent")

    assert agent["name"] == "Example Service Operations Agent"
    assert agent["release_status"] == "draft"


def test_agent_registry_show_unknown_agent_raises() -> None:
    root = Path(__file__).resolve().parents[2]

    with pytest.raises(ValueError, match="agente no registrado missing-agent"):
        AgentRegistry(root, business_pack_id="example-service").get_agent("missing-agent")


def test_agent_registry_detects_invalid_version(tmp_path: Path) -> None:
    agent_dir = write_minimal_agent(tmp_path, version="v1")

    findings = AgentRegistry(tmp_path).validate_repository()

    assert any(
        f"{agent_dir.relative_to(tmp_path).as_posix()}/agent.yaml: "
        "version debe usar formato N.N.N" in finding["message"]
        for finding in findings
    )
    assert any("agent.schema.json" in finding["message"] for finding in findings)


def test_agent_registry_detects_owner_mismatch_in_pack(tmp_path: Path) -> None:
    pack_agent_dir = tmp_path / "business_packs" / "sample-pack" / "agents" / "sample-agent"
    write_minimal_agent(tmp_path, root_agent_dir=pack_agent_dir, owner="other-owner")
    write_pack_manifest(tmp_path, agent_path=pack_agent_dir)

    findings = AgentRegistry(tmp_path, business_pack_id="sample-pack").validate_repository()

    assert any("owner debe ser company-director" in finding["message"] for finding in findings)


def test_agent_registry_detects_missing_workflow(tmp_path: Path) -> None:
    write_minimal_agent(tmp_path, workflows=("missing-workflow",))

    findings = AgentRegistry(tmp_path).validate_repository()

    assert any("workflow no encontrado missing-workflow" in finding["message"] for finding in findings)


def test_agent_registry_validates_workflow_schema(tmp_path: Path) -> None:
    agent_dir = write_minimal_agent(tmp_path)
    workflow_path = agent_dir / "workflows" / "sample-workflow.yaml"
    workflow_path.write_text(
        """
        workflow:
          id: sample-workflow
          steps:
            - checkpoint: invalid_step_without_type
        """,
        encoding="utf-8",
    )

    findings = AgentRegistry(tmp_path).validate_repository()

    assert any("workflow.schema.json" in finding["message"] for finding in findings)


def test_agent_registry_detects_missing_skill(tmp_path: Path) -> None:
    write_minimal_agent(tmp_path, skills=("missing-skill",))

    findings = AgentRegistry(tmp_path).validate_repository()

    assert any("skill no encontrada missing-skill" in finding["message"] for finding in findings)


def test_framework_validator_uses_agent_registry_for_agents(tmp_path: Path) -> None:
    write_minimal_agent(tmp_path, version="invalid")

    result = FrameworkValidator(tmp_path).validate_repository()

    assert result["status"] == "blocked"
    assert any(
        "agent.yaml: version debe usar formato N.N.N" in finding["message"]
        for finding in result["findings"]
    )


def write_minimal_agent(
    tmp_path: Path,
    *,
    root_agent_dir: Path | None = None,
    version: str = "0.1.0",
    owner: str = "company-director",
    skills: tuple[str, ...] = (),
    workflows: tuple[str, ...] = ("sample-workflow",),
) -> Path:
    agent_dir = root_agent_dir or tmp_path / "agents" / "sample-agent"
    workflow_dir = agent_dir / "workflows"
    workflow_dir.mkdir(parents=True)
    (agent_dir / "agent.yaml").write_text(
        dedent(
            f"""
            agent:
              id: sample-agent
              name: Sample Agent
              version: {version}
              domain: sample
              purpose: Validate agent registry behavior.
              owner: {owner}
              autonomy: supervised
              skills:
            {yaml_list(skills)}
              workflows:
            {yaml_list(workflows)}
            """
        ).strip(),
        encoding="utf-8",
    )
    if "sample-workflow" in workflows:
        (workflow_dir / "sample-workflow.yaml").write_text(
            dedent(
                """
                workflow:
                  id: sample-workflow
                  steps: []
                """
            ).strip(),
            encoding="utf-8",
        )
    return agent_dir


def write_pack_manifest(tmp_path: Path, *, agent_path: Path) -> None:
    pack_dir = tmp_path / "business_packs" / "sample-pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "pack.yaml").write_text(
        dedent(
            f"""
            business_pack:
              id: sample-pack
              name: Sample Pack
              version: 0.1.0
              owner_role: company-director
              purpose: Sample pack.
              domain_assets:
                agents:
                  - {agent_path.relative_to(tmp_path).as_posix()}
                context: []
                policies: []
                handoffs: []
            """
        ).strip(),
        encoding="utf-8",
    )


def yaml_list(values: tuple[str, ...]) -> str:
    if not values:
        return "                []"
    return "\n".join(f"                - {value}" for value in values)
