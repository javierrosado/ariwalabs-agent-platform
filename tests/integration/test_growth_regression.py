import json
from pathlib import Path
from typing import Any

import pytest

from ariwalabs.runtime import AgentRuntime

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests/fixtures/regression/growth"


@pytest.mark.parametrize(
    ("fixture_name", "expectation"),
    [
        (
            "campaign.json",
            {
                "status": "pending_human_approval",
                "workflow_status": "paused_for_approval",
                "approval_checkpoint": "approve_campaign",
                "artifact_types": [],
                "required_skill_refs": {
                    "growth-marketing.request-validation",
                    "growth-marketing.audience-segmentation",
                    "growth-marketing.value-proposition",
                    "growth-marketing.campaign-design",
                    "growth-marketing.content-planning",
                    "growth-marketing.brand-compliance",
                },
                "required_actions": set(),
            },
        ),
        (
            "bootcamp.json",
            {
                "status": "pending_human_approval",
                "workflow_status": "paused_for_approval",
                "approval_checkpoint": "approve_bootcamp",
                "artifact_types": [],
                "required_skill_refs": {
                    "growth-marketing.request-validation",
                    "growth-marketing.audience-segmentation",
                    "growth-marketing.value-proposition",
                    "growth-marketing.bootcamp-planning",
                    "growth-marketing.content-planning",
                    "growth-marketing.brand-compliance",
                },
                "required_actions": set(),
            },
        ),
        (
            "journey.json",
            {
                "status": "completed",
                "workflow_status": "completed",
                "approval_checkpoint": None,
                "artifact_types": ["journey_state"],
                "required_skill_refs": {
                    "growth-marketing.student-journey",
                    "growth-marketing.referral-program",
                },
                "required_actions": {"persist_state"},
            },
        ),
        (
            "opportunity.json",
            {
                "status": "pending_human_approval",
                "workflow_status": "paused_for_approval",
                "approval_checkpoint": "approve_opportunity_registration",
                "artifact_types": [],
                "required_skill_refs": {
                    "growth-marketing.request-validation",
                    "growth-marketing.corporate-opportunity-detection",
                },
                "required_actions": set(),
            },
        ),
    ],
)
def test_growth_regression_fixture(
    fixture_name: str,
    expectation: dict[str, Any],
) -> None:
    request = json.loads((FIXTURE_ROOT / fixture_name).read_text(encoding="utf-8"))

    result = AgentRuntime(ROOT).run(request)

    assert result["agent_id"] == "growth-marketing-agent"
    assert result["workflow_id"] == request["workflow_id"]
    assert result["requested_by"] == "company-director"
    assert result["status"] == expectation["status"]
    assert result["workflow_execution"]["status"] == expectation["workflow_status"]
    assert result["structured_output_error"] is None

    approval_checkpoint = expectation["approval_checkpoint"]
    if approval_checkpoint is None:
        assert result["approval"]["required"] is False
    else:
        assert result["approval"]["required"] is True
        assert result["approval"]["checkpoint"] == approval_checkpoint
        assert result["approval"]["approval_id"].startswith("appr-")

    artifact_types = [artifact["artifact_type"] for artifact in result["artifacts"]]
    assert artifact_types == expectation["artifact_types"]

    steps = result["workflow_execution"]["steps"]
    assert expectation["required_skill_refs"].issubset(_skill_refs(steps))
    assert expectation["required_actions"].issubset(_actions(steps))


def test_growth_regression_fixtures_are_loadable_requests() -> None:
    fixture_names = {path.name for path in FIXTURE_ROOT.glob("*.json")}

    assert fixture_names == {
        "bootcamp.json",
        "campaign.json",
        "journey.json",
        "opportunity.json",
    }
    for fixture_path in FIXTURE_ROOT.glob("*.json"):
        request = json.loads(fixture_path.read_text(encoding="utf-8"))
        assert request["agent_id"] == "growth-marketing-agent"
        assert request["requested_by"] == "company-director"
        assert isinstance(request["input"], dict)


def _skill_refs(steps: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for step in _walk_steps(steps):
        ref = step.get("ref")
        if step.get("type") == "skill" and isinstance(ref, str):
            refs.add(ref)
    return refs


def _actions(steps: list[dict[str, Any]]) -> set[str]:
    actions: set[str] = set()
    for step in _walk_steps(steps):
        action = step.get("action")
        if step.get("type") == "action" and isinstance(action, str):
            actions.add(action)
    return actions


def _walk_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    walked: list[dict[str, Any]] = []
    for step in steps:
        walked.append(step)
        nested = step.get("step")
        if isinstance(nested, dict):
            walked.extend(_walk_steps([nested]))
        for child_key in ("branches", "steps"):
            children = step.get(child_key)
            if isinstance(children, list):
                walked.extend(
                    _walk_steps(
                        [child for child in children if isinstance(child, dict)],
                    ),
                )
    return walked
