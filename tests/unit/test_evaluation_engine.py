from pathlib import Path
from textwrap import dedent
from typing import Any

from adapters.models.base import ModelResult
from ariwalabs.evaluation_engine import EvaluationEngine


def test_evaluation_engine_accepts_repository_rubrics() -> None:
    root = Path(__file__).resolve().parents[2]

    findings = EvaluationEngine(root).validate_repository()

    assert findings == []


def test_evaluation_engine_blocks_missing_agent_rubrics(tmp_path: Path) -> None:
    write_minimal_agent(tmp_path)

    findings = EvaluationEngine(tmp_path).validate_repository()

    assert any(
        "sample-agent: falta evaluations/rubrics.yaml" in finding["message"]
        for finding in findings
    )


def test_evaluation_engine_evaluates_valid_skill_output() -> None:
    root = Path(__file__).resolve().parents[2]
    result = EvaluationEngine(root).evaluate_workflow(
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        workflow_execution={
            "steps": [
                {
                    "type": "skill",
                    "ref": "growth-marketing.brand-compliance",
                    "status": "completed",
                    "model_result": {
                        "status": "completed",
                        "content": brand_compliance_output(),
                    },
                }
            ]
        },
        correlation_id="exec-test",
    )

    evaluation = result["skill_evaluations"][0]
    assert result["status"] == "passed"
    assert evaluation["status"] == "passed"
    assert evaluation["score"] == 1.0
    assert evaluation["model_evaluation"]["status"] == "skipped"


def test_evaluation_engine_invokes_model_gateway_separately() -> None:
    root = Path(__file__).resolve().parents[2]
    model_gateway = RecordingEvaluationGateway()

    result = EvaluationEngine(root, model_gateway=model_gateway).evaluate_workflow(
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        workflow_execution={
            "steps": [
                {
                    "type": "skill",
                    "ref": "growth-marketing.brand-compliance",
                    "status": "completed",
                    "model_result": {
                        "status": "completed",
                        "content": brand_compliance_output(),
                    },
                }
            ]
        },
        correlation_id="exec-test",
    )

    evaluation = result["skill_evaluations"][0]
    assert model_gateway.calls[0]["profile"] == "evaluation"
    assert model_gateway.calls[0]["skill_id"] == "growth-marketing.brand-compliance"
    assert evaluation["model_evaluation"]["content"]["score"] == 1.0


def test_evaluation_engine_blocks_schema_mismatch() -> None:
    root = Path(__file__).resolve().parents[2]
    invalid_output = brand_compliance_output()
    invalid_output.pop("summary")

    result = EvaluationEngine(root).evaluate_workflow(
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        workflow_execution={
            "steps": [
                {
                    "type": "skill",
                    "ref": "growth-marketing.brand-compliance",
                    "status": "completed",
                    "model_result": {
                        "status": "completed",
                        "content": invalid_output,
                    },
                }
            ]
        },
    )

    evaluation = result["skill_evaluations"][0]
    assert result["status"] == "blocked"
    assert evaluation["status"] == "blocked"
    assert any("required property" in error for error in evaluation["errors"])


class RecordingEvaluationGateway:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_structured(
        self,
        *,
        profile: str,
        system_prompt: str,
        payload: dict[str, Any],
        output_schema: dict[str, Any],
        correlation_id: str | None = None,
        skill_id: str | None = None,
    ) -> ModelResult:
        self.calls.append(
            {
                "profile": profile,
                "system_prompt": system_prompt,
                "payload": payload,
                "output_schema": output_schema,
                "correlation_id": correlation_id,
                "skill_id": skill_id,
            }
        )
        return {
            "status": "completed",
            "profile": profile,
            "content": {
                "status": "passed",
                "score": 1.0,
                "findings": [],
                "recommendations": [],
                "errors": [],
            },
            "error": None,
        }


def brand_compliance_output() -> dict[str, Any]:
    return {
        "status": "passed",
        "summary": "Cumple politicas.",
        "checks": [
            {
                "name": "claims",
                "result": "passed",
                "notes": "Sin claims inventados.",
            }
        ],
        "violations": [],
        "facts": ["Programa con tres niveles."],
        "assumptions": [],
        "risks": [],
        "missing_information": [],
        "approval_required": False,
        "approval_reason": None,
        "errors": [],
        "next_actions": ["Preparar revision humana si aplica."],
    }


def write_minimal_agent(root: Path) -> None:
    agent_dir = root / "agents" / "sample-agent"
    skill_dir = agent_dir / "skills" / "sample-skill"
    skill_dir.mkdir(parents=True)
    (agent_dir / "agent.yaml").write_text(
        dedent(
            """
            agent:
              id: sample-agent
              name: Sample Agent
              version: 0.1.0
              purpose: Validate evaluation behavior.
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
