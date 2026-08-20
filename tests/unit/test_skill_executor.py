from pathlib import Path
from textwrap import dedent

import pytest

from adapters.models.fake import FakeModelAdapter
from ariwalabs.context_engine import ContextEngine
from ariwalabs.model_gateway import ModelGateway
from ariwalabs.skill_executor import SkillExecutionRequest, SkillExecutor
from ariwalabs.workflow_engine import WorkflowEngine


def test_skill_executor_runs_default_agent_skill_with_model_gateway() -> None:
    root = Path(__file__).resolve().parents[2]
    composed_context = ContextEngine(root).compose_for_agent_workflow(
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
    )
    executor = SkillExecutor(
        root,
        model_gateway=ModelGateway(adapter=FakeModelAdapter(), root=root),
    )

    result = executor.execute(
        SkillExecutionRequest(
            agent_id="growth-marketing-agent",
            workflow_id="create-training-campaign",
            skill_id="growth-marketing.request-validation",
            business_pack_id=None,
            request_input={"objective": "Test campaign"},
            composed_context=composed_context.to_dict(),
            correlation_id="exec-test",
        )
    )

    assert result["status"] == "draft"
    assert result["profile"] == "fast_structured"
    assert result["content"]["status"] == "valid"
    assert result["content"]["validated_input"]["objective"] == "fake model response"


def test_skill_executor_runs_business_pack_skill_with_model_gateway() -> None:
    root = Path(__file__).resolve().parents[2]
    composed_context = ContextEngine(
        root,
        business_pack_id="ariwalabs-training",
    ).compose_for_agent_workflow(
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
    )
    executor = SkillExecutor(
        root,
        business_pack_id="ariwalabs-training",
        model_gateway=ModelGateway(adapter=FakeModelAdapter(), root=root),
    )

    result = executor.execute(
        SkillExecutionRequest(
            agent_id="growth-marketing-agent",
            workflow_id="create-training-campaign",
            skill_id="growth-marketing.request-validation",
            business_pack_id="ariwalabs-training",
            request_input={"objective": "Test campaign"},
            composed_context=composed_context.to_dict(),
            correlation_id="exec-test",
        )
    )

    assert result["status"] == "draft"
    assert result["content"]["summary"] == "fake model response"


def test_workflow_engine_executes_skill_with_executor() -> None:
    root = Path(__file__).resolve().parents[2]
    composed_context = ContextEngine(root).compose_for_agent_workflow(
        agent_id="growth-marketing-agent",
        workflow_id="manage-student-growth-journey",
    )
    executor = SkillExecutor(
        root,
        model_gateway=ModelGateway(adapter=FakeModelAdapter(), root=root),
    )

    result = WorkflowEngine(
        root,
        skill_executor=executor,
        composed_context=composed_context.to_dict(),
        correlation_id="exec-test",
    ).run(
        agent_id="growth-marketing-agent",
        workflow_id="manage-student-growth-journey",
        request_input={"objective": "Journey"},
    )

    assert result["status"] == "completed"
    assert result["steps"][0]["status"] == "completed"
    assert result["steps"][0]["model_result"]["profile"] == "reasoning"


def test_workflow_engine_keeps_injected_skill_results_precedence() -> None:
    root = Path(__file__).resolve().parents[2]
    composed_context = ContextEngine(root).compose_for_agent_workflow(
        agent_id="growth-marketing-agent",
        workflow_id="manage-student-growth-journey",
    )
    executor = SkillExecutor(
        root,
        model_gateway=ModelGateway(adapter=FakeModelAdapter(), root=root),
    )
    injected = {
        "status": "completed",
        "profile": "generation",
        "provider": "test",
        "model": "fixture",
        "content": {"fixture": True},
    }

    result = WorkflowEngine(
        root,
        skill_executor=executor,
        composed_context=composed_context.to_dict(),
        correlation_id="exec-test",
    ).run(
        agent_id="growth-marketing-agent",
        workflow_id="manage-student-growth-journey",
        request_input={
            "__skill_results__": {
                "growth-marketing.student-journey": injected,
            },
        },
    )

    assert result["steps"][0]["model_result"] == injected


def test_skill_executor_blocks_missing_prompt(tmp_path: Path) -> None:
    write_agent_without_prompt(tmp_path)
    executor = SkillExecutor(
        tmp_path,
        model_gateway=ModelGateway(adapter=FakeModelAdapter(), root=tmp_path),
    )

    with pytest.raises(ValueError, match="prompt inexistente"):
        executor.execute(
            SkillExecutionRequest(
                agent_id="sample-agent",
                workflow_id="sample-workflow",
                skill_id="sample.sample-skill",
                business_pack_id=None,
                request_input={},
                composed_context={},
            )
        )


def write_agent_without_prompt(root: Path) -> None:
    agent_dir = root / "agents" / "sample-agent"
    skill_dir = agent_dir / "skills" / "sample-skill"
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
              purpose: Test missing prompt.
              owner: company-director
              autonomy: supervised
              skills:
                - sample-skill
              workflows: []
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
    (schema_dir / "sample.schema.json").write_text(
        '{"title":"sample","type":"object","required":["summary"],'
        '"properties":{"summary":{"type":"string"}},"additionalProperties":false}',
        encoding="utf-8",
    )
