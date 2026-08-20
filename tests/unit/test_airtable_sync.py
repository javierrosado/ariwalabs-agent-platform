from pathlib import Path
from typing import Any

from ariwalabs.airtable_sync import AirtableSync
from ariwalabs.approval_engine import ApprovalEngine
from ariwalabs.artifact_manager import ArtifactManager
from ariwalabs.repository import JsonRepository


class FakeAirtableSyncAdapter:
    def __init__(self) -> None:
        self.created: list[dict[str, Any]] = []

    def create_draft(
        self,
        table: str,
        fields: dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        self.created.append(
            {
                "table": table,
                "fields": fields,
                "idempotency_key": idempotency_key,
            }
        )
        return {
            "id": f"rec-{len(self.created)}",
            "fields": fields,
        }


def test_airtable_sync_writes_execution_approval_and_artifacts(tmp_path: Path) -> None:
    repo = JsonRepository(tmp_path / "runtime/data")
    execution = execution_payload()
    repo.save("executions", "exec-test", execution)
    approval = ApprovalEngine(tmp_path).create_pending(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        checkpoint="approve_campaign",
        approver="company-director",
    )
    execution["approval"] = {
        **execution["approval"],
        "approval_id": approval["approval_id"],
    }
    artifact = ArtifactManager(tmp_path).create(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        artifact_type="workflow_artifacts",
        source_action="persist_artifacts",
        status="pending_approval",
    )
    execution["artifacts"] = [artifact]
    repo.save("executions", "exec-test", execution)
    adapter = FakeAirtableSyncAdapter()

    result = AirtableSync(tmp_path, adapter=adapter).sync_execution("exec-test")

    assert result["status"] == "synced"
    assert result["records_count"] == 3
    assert [item["table"] for item in adapter.created] == [
        "AgentExecutions",
        "Approvals",
        "Artifacts",
    ]
    assert adapter.created[0]["fields"]["ExecutionId"] == "exec-test"
    assert adapter.created[0]["idempotency_key"] == "AgentExecutions:exec-test"
    assert adapter.created[1]["idempotency_key"] == f"Approvals:{approval['approval_id']}"
    assert adapter.created[2]["idempotency_key"] == f"Artifacts:{artifact['artifact_id']}"


def test_airtable_sync_writes_execution_without_related_records(tmp_path: Path) -> None:
    JsonRepository(tmp_path / "runtime/data").save("executions", "exec-test", execution_payload())
    adapter = FakeAirtableSyncAdapter()

    result = AirtableSync(tmp_path, adapter=adapter).sync_execution("exec-test")

    assert result["records_count"] == 1
    assert adapter.created[0]["table"] == "AgentExecutions"


def test_airtable_sync_uses_decided_approval_payload(tmp_path: Path) -> None:
    repo = JsonRepository(tmp_path / "runtime/data")
    execution = execution_payload()
    repo.save("executions", "exec-test", execution)
    approval = ApprovalEngine(tmp_path).create_pending(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="create-training-campaign",
        checkpoint="approve_campaign",
        approver="company-director",
    )
    decided = ApprovalEngine(tmp_path).decide(
        approval_id=approval["approval_id"],
        decision="approved",
        reason="Aprobado para prueba.",
        decided_by="company-director",
    )
    execution = repo.load("executions", "exec-test")
    execution["agent_id"] = "growth-marketing-agent"
    execution["agent_version"] = "0.2.0"
    execution["workflow_id"] = "create-training-campaign"
    execution["requested_by"] = "company-director"
    execution["created_at"] = "2026-08-15T00:00:00+00:00"
    execution["workflow_execution"] = {"status": "paused_for_approval"}
    repo.save("executions", "exec-test", execution)
    adapter = FakeAirtableSyncAdapter()

    AirtableSync(tmp_path, adapter=adapter).sync_execution("exec-test")

    approval_fields = adapter.created[1]["fields"]
    assert approval_fields["Decision"] == "approved"
    assert approval_fields["Reason"] == "Aprobado para prueba."
    assert approval_fields["DecidedBy"] == "company-director"
    assert approval_fields["DecidedAt"] == decided["decided_at"]


def test_airtable_sync_requires_execution_fields(tmp_path: Path) -> None:
    JsonRepository(tmp_path / "runtime/data").save(
        "executions",
        "exec-test",
        {"execution_id": "exec-test"},
    )

    try:
        AirtableSync(tmp_path, adapter=FakeAirtableSyncAdapter()).sync_execution("exec-test")
    except ValueError as exc:
        assert "agent_id requerido" in str(exc)
    else:
        raise AssertionError("execution incompleta debio fallar")


def execution_payload() -> dict[str, Any]:
    return {
        "execution_id": "exec-test",
        "agent_id": "growth-marketing-agent",
        "agent_version": "0.2.0",
        "workflow_id": "create-training-campaign",
        "requested_by": "company-director",
        "created_at": "2026-08-15T00:00:00+00:00",
        "status": "pending_human_approval",
        "workflow_execution": {"status": "paused_for_approval"},
        "approval": {},
        "artifacts": [],
    }
