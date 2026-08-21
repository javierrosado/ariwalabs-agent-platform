from pathlib import Path

from ariwalabs.schema_validator import CoreSchemaValidator


def test_core_schema_validator_accepts_valid_agent_payload(tmp_path: Path) -> None:
    payload = {
        "agent": {
            "id": "sample-agent",
            "name": "Sample Agent",
            "version": "0.1.0",
            "purpose": "Validate a sample agent.",
            "owner": "company-director",
            "autonomy": "supervised",
            "skills": [],
            "workflows": ["sample-workflow"],
        }
    }

    findings = CoreSchemaValidator(tmp_path).validate_payload(
        payload=payload,
        schema_name="agent.schema.json",
        source_path=tmp_path / "agents/sample-agent/agent.yaml",
    )

    assert findings == []


def test_core_schema_validator_blocks_extra_agent_property(tmp_path: Path) -> None:
    payload = {
        "agent": {
            "id": "sample-agent",
            "name": "Sample Agent",
            "version": "0.1.0",
            "purpose": "Validate a sample agent.",
            "owner": "company-director",
            "autonomy": "supervised",
            "skills": [],
            "workflows": ["sample-workflow"],
            "unexpected": True,
        }
    }

    findings = CoreSchemaValidator(tmp_path).validate_payload(
        payload=payload,
        schema_name="agent.schema.json",
        source_path=tmp_path / "agents/sample-agent/agent.yaml",
    )

    assert any("Additional properties are not allowed" in finding["message"] for finding in findings)


def test_core_schema_validator_blocks_invalid_workflow_step(tmp_path: Path) -> None:
    payload = {
        "workflow": {
            "id": "sample-workflow",
            "steps": [
                {"checkpoint": "missing_step_type"},
            ],
        }
    }

    findings = CoreSchemaValidator(tmp_path).validate_payload(
        payload=payload,
        schema_name="workflow.schema.json",
        source_path=tmp_path / "agents/sample-agent/workflows/sample-workflow.yaml",
    )

    assert any("not valid under any of the given schemas" in finding["message"] for finding in findings)
