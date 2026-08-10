from pathlib import Path
from textwrap import dedent

from ariwalabs.framework_validator import FrameworkValidator


def test_repository_is_valid() -> None:
    root = Path(__file__).resolve().parents[2]
    result = FrameworkValidator(root).validate_repository()
    assert result["status"] != "blocked", result


def test_repository_schemas_are_strict() -> None:
    root = Path(__file__).resolve().parents[2]
    result = FrameworkValidator(root).validate_repository()
    messages = [finding["message"] for finding in result["findings"]]

    assert not any("required debe ser una lista no vacia" in message for message in messages)
    assert not any("additionalProperties debe ser false" in message for message in messages)
    assert not any("additionalProperties true no permitido" in message for message in messages)


def test_validator_blocks_permissive_skill_schema(tmp_path: Path) -> None:
    agent_dir = tmp_path / "agents" / "sample-agent"
    skill_dir = agent_dir / "skills" / "sample-skill"
    schema_dir = agent_dir / "schemas"
    workflow_dir = agent_dir / "workflows"
    skill_dir.mkdir(parents=True)
    schema_dir.mkdir()
    workflow_dir.mkdir()

    (agent_dir / "agent.yaml").write_text(
        dedent(
            """
            agent:
              id: sample-agent
              name: Sample Agent
              version: 0.1.0
              purpose: Validate schema behavior.
              owner: company-director
              autonomy: supervised
              skills:
                - sample-skill
              workflows:
                - sample-workflow
            """
        ).strip(),
        encoding="utf-8",
    )
    (skill_dir / "skill.yaml").write_text(
        dedent(
            """
            skill:
              id: sample.sample-skill
              version: 0.1.0
              purpose: Sample skill.
              model_profile: fast_structured
              approval_required: false
              output_schema: ../../schemas/sample.schema.json
            """
        ).strip(),
        encoding="utf-8",
    )
    (workflow_dir / "sample-workflow.yaml").write_text(
        dedent(
            """
            workflow:
              id: sample-workflow
              steps:
                - skill: sample.sample-skill
            """
        ).strip(),
        encoding="utf-8",
    )
    (schema_dir / "sample.schema.json").write_text(
        dedent(
            """
            {
              "$schema": "https://json-schema.org/draft/2020-12/schema",
              "title": "sample",
              "type": "object",
              "additionalProperties": true
            }
            """
        ).strip(),
        encoding="utf-8",
    )

    result = FrameworkValidator(tmp_path).validate_repository()

    assert result["status"] == "blocked"
    messages = [finding["message"] for finding in result["findings"]]
    assert any("required debe ser una lista no vacia" in message for message in messages)
    assert any("properties debe ser un objeto no vacio" in message for message in messages)
    assert any("additionalProperties debe ser false" in message for message in messages)
