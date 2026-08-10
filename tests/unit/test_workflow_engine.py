from pathlib import Path

from ariwalabs.workflow_engine import WorkflowEngine


def test_workflow_engine_pauses_campaign_for_approval() -> None:
    root = Path(__file__).resolve().parents[2]
    result = WorkflowEngine(root).run(
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        request_input={"objective": "Test campaign"},
    )

    assert result["status"] == "paused_for_approval"
    assert result["approval"]["checkpoint"] == "approve_campaign"
    assert any(step["type"] == "parallel" for step in result["steps"])


def test_workflow_engine_skips_unmatched_condition() -> None:
    root = Path(__file__).resolve().parents[2]
    result = WorkflowEngine(root).run(
        agent_id="growth-marketing-agent",
        workflow_id="manage-student-growth-journey",
        request_input={},
    )

    assert result["status"] == "completed"
    assert result["steps"][1]["type"] == "condition"
    assert result["steps"][1]["status"] == "skipped"


def test_workflow_engine_runs_matched_condition() -> None:
    root = Path(__file__).resolve().parents[2]
    result = WorkflowEngine(root).run(
        agent_id="growth-marketing-agent",
        workflow_id="manage-student-growth-journey",
        request_input={"eligible_for_referral": True},
    )

    assert result["status"] == "completed"
    assert result["steps"][1]["type"] == "condition"
    assert result["steps"][1]["status"] == "simulated"
    assert result["steps"][1]["step"]["ref"] == "growth-marketing.referral-program"


def test_workflow_engine_blocks_external_action(tmp_path: Path) -> None:
    write_minimal_agent(tmp_path, action="publish_content")

    result = WorkflowEngine(tmp_path).run(
        agent_id="sample-agent",
        workflow_id="sample-workflow",
        request_input={},
    )

    assert result["status"] == "blocked"
    assert "accion externa prohibida publish_content" in result["errors"]


def test_workflow_engine_blocks_invalid_approval_approver(tmp_path: Path) -> None:
    write_minimal_agent(tmp_path, approval="other-approver")

    result = WorkflowEngine(tmp_path).run(
        agent_id="sample-agent",
        workflow_id="sample-workflow",
        request_input={},
    )

    assert result["status"] == "blocked"
    assert "approval debe ser company-director" in result["errors"]


def test_workflow_engine_pauses_on_invalid_structured_output() -> None:
    root = Path(__file__).resolve().parents[2]
    result = WorkflowEngine(root).run(
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        request_input={
            "objective": "Test campaign",
            "__skill_results__": {
                "growth-marketing.request-validation": {
                    "status": "invalid_output",
                    "profile": "fast_structured",
                    "provider": "openai",
                    "model": "gpt-test",
                    "error": {
                        "type": "ModelOutputError",
                        "message": "schema mismatch",
                        "retryable": True,
                    },
                },
            },
        },
    )

    assert result["status"] == "needs_structured_output_review"
    assert result["steps"][0]["status"] == "failed_recoverable"
    assert result["steps"][0]["model_result"]["error"]["skill_id"] == (
        "growth-marketing.request-validation"
    )
    assert result["steps"][0]["model_result"]["error"]["retryable"] is True
    assert result["approval"] is None


def write_minimal_agent(
    root: Path,
    *,
    action: str | None = None,
    approval: str | None = None,
) -> None:
    agent_dir = root / "agents" / "sample-agent"
    workflow_dir = agent_dir / "workflows"
    skill_dir = agent_dir / "skills" / "sample-skill"
    workflow_dir.mkdir(parents=True)
    skill_dir.mkdir(parents=True)
    (agent_dir / "agent.yaml").write_text(
        """
agent:
  id: sample-agent
  name: Sample Agent
  version: 0.1.0
  purpose: Validate workflow behavior.
  owner: company-director
  autonomy: supervised
  skills:
    - sample-skill
  workflows:
    - sample-workflow
""".strip(),
        encoding="utf-8",
    )
    (skill_dir / "skill.yaml").write_text(
        """
skill:
  id: sample.sample-skill
  version: 0.1.0
  purpose: Sample skill.
  model_profile: fast_structured
  approval_required: false
  output_schema: ../../schemas/sample.schema.json
""".strip(),
        encoding="utf-8",
    )
    step = f"    - action: {action}" if action else f"    - approval: {approval}"
    checkpoint = "" if action else "\n      checkpoint: approve_sample"
    (workflow_dir / "sample-workflow.yaml").write_text(
        f"""
workflow:
  id: sample-workflow
  steps:
{step}{checkpoint}
""".strip(),
        encoding="utf-8",
    )
