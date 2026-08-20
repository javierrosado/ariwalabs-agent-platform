from pathlib import Path

import pytest

from ariwalabs.errors import ToolApprovalRequiredError, ToolExecutionError
from ariwalabs.repository import JsonRepository
from ariwalabs.tool_gateway import ToolExecutionRequest, ToolGateway


def test_tool_gateway_accepts_known_allowed_and_prohibited_tools(tmp_path: Path) -> None:
    skill_path = tmp_path / "agents" / "sample-agent" / "skills" / "sample" / "skill.yaml"
    skill_path.parent.mkdir(parents=True)
    gateway = ToolGateway(tmp_path)

    findings = gateway.validate_skill_tools(
        skill_path=skill_path,
        allowed=("airtable-read", "artifact-create", "audit-append"),
        prohibited=("external-message", "external-publish"),
    )

    assert findings == []


def test_tool_gateway_blocks_overlap(tmp_path: Path) -> None:
    skill_path = tmp_path / "agents" / "sample-agent" / "skills" / "sample" / "skill.yaml"
    skill_path.parent.mkdir(parents=True)
    gateway = ToolGateway(tmp_path)

    findings = gateway.validate_skill_tools(
        skill_path=skill_path,
        allowed=("audit-append",),
        prohibited=("audit-append",),
    )

    assert any(
        "tools simultaneamente permitidas y prohibidas: ['audit-append']" in finding["message"]
        for finding in findings
    )


def test_tool_gateway_blocks_external_action_as_allowed_tool(tmp_path: Path) -> None:
    skill_path = tmp_path / "agents" / "sample-agent" / "skills" / "sample" / "skill.yaml"
    skill_path.parent.mkdir(parents=True)
    gateway = ToolGateway(tmp_path)

    findings = gateway.validate_skill_tools(
        skill_path=skill_path,
        allowed=("external-publish",),
        prohibited=(),
    )

    assert any(
        "tools prohibidas en allowed: ['external-publish']" in finding["message"]
        for finding in findings
    )


def test_tool_gateway_blocks_unknown_tools(tmp_path: Path) -> None:
    skill_path = tmp_path / "agents" / "sample-agent" / "skills" / "sample" / "skill.yaml"
    skill_path.parent.mkdir(parents=True)
    gateway = ToolGateway(tmp_path)

    findings = gateway.validate_skill_tools(
        skill_path=skill_path,
        allowed=("unknown-tool",),
        prohibited=("unknown-prohibited-tool",),
    )

    assert any(
        "tools allowed desconocidas: ['unknown-tool']" in finding["message"]
        for finding in findings
    )
    assert any(
        "tools prohibited desconocidas: ['unknown-prohibited-tool']" in finding["message"]
        for finding in findings
    )


def test_tool_gateway_resolves_catalog_metadata(tmp_path: Path) -> None:
    gateway = ToolGateway(tmp_path)

    resolution = gateway.resolve(
        allowed=("airtable-read", "audit-append"),
        prohibited=("external-message",),
    )

    assert [tool.tool_id for tool in resolution.allowed] == ["airtable-read", "audit-append"]
    assert resolution.allowed[0].adapter == "airtable"
    assert resolution.allowed[0].external is True
    assert resolution.allowed[1].external is False
    assert resolution.prohibited[0].allowed_in_skills is False


def test_tool_gateway_executes_audit_append_with_duration(tmp_path: Path) -> None:
    gateway = ToolGateway(tmp_path)

    result = gateway.execute(
        ToolExecutionRequest(
            tool_id="audit-append",
            payload={"event_type": "sample.event", "payload": {"ok": True}},
            actor="company-director",
            correlation_id="exec-test",
        )
    )

    assert result.status == "completed"
    assert result.output["event"]["event_type"] == "sample.event"
    assert result.duration_ms >= 0


def test_tool_gateway_executes_artifact_create(tmp_path: Path) -> None:
    gateway = ToolGateway(tmp_path)

    result = gateway.execute(
        ToolExecutionRequest(
            tool_id="artifact-create",
            payload={
                "execution_id": "exec-test",
                "agent_id": "growth-marketing-agent",
                "workflow_id": "create-training-campaign",
                "artifact_type": "workflow_artifacts",
                "source_action": "persist_artifacts",
                "status": "draft",
            },
            correlation_id="exec-test",
        )
    )
    artifact = result.output["artifact"]
    persisted = JsonRepository(tmp_path / "runtime/data").load(
        "artifacts",
        artifact["artifact_id"],
    )

    assert artifact["artifact_type"] == "workflow_artifacts"
    assert persisted["artifact_id"] == artifact["artifact_id"]


def test_tool_gateway_blocks_unapproved_external_write(tmp_path: Path) -> None:
    gateway = ToolGateway(tmp_path, adapters={"airtable": FakeAirtableAdapter()})

    with pytest.raises(ToolApprovalRequiredError):
        gateway.execute(
            ToolExecutionRequest(
                tool_id="airtable-write-draft",
                payload={"table": "AgentExecutions", "fields": {"Name": "Draft"}},
            )
        )


def test_tool_gateway_executes_approved_airtable_write(tmp_path: Path) -> None:
    adapter = FakeAirtableAdapter()
    gateway = ToolGateway(tmp_path, adapters={"airtable": adapter})

    result = gateway.execute(
        ToolExecutionRequest(
            tool_id="airtable-write-draft",
            payload={
                "table": "AgentExecutions",
                "fields": {"Name": "Draft"},
                "idempotency_key": "tool-test",
            },
            approved=True,
        )
    )

    assert result.external is True
    assert result.adapter == "airtable"
    assert result.output["record"]["id"] == "rec-AgentExecutions"
    assert adapter.created[0]["idempotency_key"] == "tool-test"


def test_tool_gateway_requires_configured_adapter(tmp_path: Path) -> None:
    gateway = ToolGateway(tmp_path)

    with pytest.raises(ToolExecutionError):
        gateway.execute(
            ToolExecutionRequest(
                tool_id="airtable-read",
                payload={"table": "AgentExecutions"},
            )
        )


class FakeAirtableAdapter:
    def __init__(self) -> None:
        self.created: list[dict[str, object]] = []

    def list_records(self, table: str, **filters: object) -> list[dict[str, object]]:
        return [{"id": f"rec-{table}", "filters": filters}]

    def create_draft(
        self,
        table: str,
        fields: dict[str, object],
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, object]:
        payload = {
            "table": table,
            "fields": fields,
            "idempotency_key": idempotency_key,
        }
        self.created.append(payload)
        return {"id": f"rec-{table}", "fields": fields}
