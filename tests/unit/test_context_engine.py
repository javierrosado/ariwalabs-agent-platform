from pathlib import Path
from textwrap import dedent

from ariwalabs.context_engine import ContextCompositionError, ContextEngine


def test_context_engine_composes_growth_agent_context() -> None:
    root = Path(__file__).resolve().parents[2]

    context = ContextEngine(root).compose_for_agent_workflow(
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
    )

    payload = context.to_dict()
    assert payload["agent_id"] == "growth-marketing-agent"
    assert payload["workflow_id"] == "create-training-campaign"
    assert payload["source_paths"] == (
        "shared/context/company-profile.yaml",
        "shared/context/training-catalog.yaml",
        "shared/context/target-audiences.yaml",
        "shared/context/channels.yaml",
        "shared/policies/global-agent-policy.yaml",
    )
    assert payload["data"]["company"]["company"]["name"] == "AriwaLabs"
    assert payload["data"]["training_catalog"]["training_catalog"]["currency"] == "PEN"
    assert payload["data"]["global_policies"]["global_policies"]["single_operator"]["enabled"]


def test_context_engine_blocks_context_outside_shared(tmp_path: Path) -> None:
    write_agent_with_context(tmp_path, ["docs/project-context.md"])

    findings = ContextEngine(tmp_path).validate_agent_context(
        agent_id="sample-agent",
        agent_config={
            "shared_context": ["docs/project-context.md"],
        },
    )

    assert any(
        "contexto fuera de rutas permitidas docs/project-context.md" in finding["message"]
        for finding in findings
    )


def test_context_engine_blocks_duplicate_context(tmp_path: Path) -> None:
    write_agent_with_context(
        tmp_path,
        ["shared/context/company-profile.yaml", "shared/context/company-profile.yaml"],
    )
    (tmp_path / "shared" / "context").mkdir(parents=True)
    (tmp_path / "shared" / "context" / "company-profile.yaml").write_text(
        "company:\n  name: AriwaLabs\n",
        encoding="utf-8",
    )

    findings = ContextEngine(tmp_path).validate_agent_context(
        agent_id="sample-agent",
        agent_config={
            "shared_context": [
                "shared/context/company-profile.yaml",
                "shared/context/company-profile.yaml",
            ],
        },
    )

    assert any(
        "contexto duplicado shared/context/company-profile.yaml" in finding["message"]
        for finding in findings
    )


def test_context_engine_raises_when_composition_is_invalid(tmp_path: Path) -> None:
    write_agent_with_context(tmp_path, ["shared/context/missing.yaml"])

    try:
        ContextEngine(tmp_path).compose_for_agent_workflow(
            agent_id="sample-agent",
            workflow_id="sample-workflow",
        )
    except ContextCompositionError as exc:
        assert any(
            "contexto inexistente shared/context/missing.yaml" in finding["message"]
            for finding in exc.findings
        )
    else:
        raise AssertionError("contexto faltante debio bloquear composicion")


def write_agent_with_context(root: Path, shared_context: list[str]) -> None:
    agent_dir = root / "agents" / "sample-agent"
    agent_dir.mkdir(parents=True)
    context_lines = "\n".join(f"                - {path}" for path in shared_context)
    (agent_dir / "agent.yaml").write_text(
        dedent(
            f"""
            agent:
              id: sample-agent
              name: Sample Agent
              version: 0.1.0
              purpose: Compose context.
              owner: company-director
              autonomy: supervised
              shared_context:
{context_lines}
              skills: []
              workflows:
                - sample-workflow
            """
        ).strip(),
        encoding="utf-8",
    )
