from pathlib import Path
from textwrap import dedent

from ariwalabs.skill_registry import SkillRegistry


def test_skill_registry_accepts_repository_skills() -> None:
    root = Path(__file__).resolve().parents[2]
    findings = SkillRegistry(root).validate_repository()

    assert findings == []


def test_skill_registry_blocks_id_folder_mismatch(tmp_path: Path) -> None:
    write_skill_fixture(
        tmp_path,
        skill_slug="sample-skill",
        skill_id="sample.other-skill",
    )

    findings = SkillRegistry(tmp_path).validate_repository()

    assert any("id debe terminar con sample-skill" in finding["message"] for finding in findings)


def test_skill_registry_blocks_forbidden_allowed_tool(tmp_path: Path) -> None:
    write_skill_fixture(
        tmp_path,
        allowed_tools=["external-publish"],
    )

    findings = SkillRegistry(tmp_path).validate_repository()

    assert any("tools prohibidas en allowed" in finding["message"] for finding in findings)


def test_skill_registry_blocks_unknown_tool(tmp_path: Path) -> None:
    write_skill_fixture(
        tmp_path,
        allowed_tools=["unknown-tool"],
    )

    findings = SkillRegistry(tmp_path).validate_repository()

    assert any(
        "tools allowed desconocidas: ['unknown-tool']" in finding["message"]
        for finding in findings
    )


def test_skill_registry_blocks_sensitive_skill_without_approval(tmp_path: Path) -> None:
    write_skill_fixture(
        tmp_path,
        skill_slug="campaign-design",
        skill_id="sample.campaign-design",
        approval_required=False,
    )

    findings = SkillRegistry(tmp_path).validate_repository()

    assert any("skill sensible requiere aprobacion" in finding["message"] for finding in findings)


def test_skill_registry_blocks_unknown_model_profile(tmp_path: Path) -> None:
    write_skill_fixture(tmp_path, model_profile="unknown")

    findings = SkillRegistry(tmp_path).validate_repository()

    assert any("model_profile no soportado unknown" in finding["message"] for finding in findings)


def write_skill_fixture(
    root: Path,
    *,
    skill_slug: str = "sample-skill",
    skill_id: str = "sample.sample-skill",
    model_profile: str = "fast_structured",
    approval_required: bool = False,
    allowed_tools: list[str] | None = None,
) -> None:
    agent_dir = root / "agents" / "sample-agent"
    skill_dir = agent_dir / "skills" / skill_slug
    schema_dir = agent_dir / "schemas"
    skill_dir.mkdir(parents=True)
    schema_dir.mkdir()

    (agent_dir / "agent.yaml").write_text(
        dedent(
            """
            agent:
              id: sample-agent
              name: Sample Agent
              version: 0.1.0
              purpose: Validate skill registry behavior.
              owner: company-director
              autonomy: supervised
              approvals:
                - campaign_release
              skills:
                - sample-skill
              workflows: []
            """
        ).strip(),
        encoding="utf-8",
    )
    (skill_dir / "skill.yaml").write_text(
        dedent(
            f"""
            skill:
              id: {skill_id}
              version: 0.1.0
              purpose: Sample skill.
              model_profile: {model_profile}
              approval_required: {str(approval_required).lower()}
              tools:
                allowed:
{format_yaml_list(allowed_tools or ["audit-append"], indent=18)}
                prohibited:
                  - external-message
              output_schema: ../../schemas/sample.schema.json
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
              "required": [
                "status",
                "errors"
              ],
              "properties": {
                "status": {
                  "type": "string"
                },
                "errors": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": false
                  }
                }
              },
              "additionalProperties": false
            }
            """
        ).strip(),
        encoding="utf-8",
    )


def format_yaml_list(values: list[str], *, indent: int) -> str:
    padding = " " * indent
    return "\n".join(f"{padding}- {value}" for value in values)
