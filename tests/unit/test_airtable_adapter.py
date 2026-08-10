import json
from pathlib import Path
from typing import Any

from adapters.airtable.client import AirtableConfig, AirtableHttpAdapter
from adapters.airtable.errors import (
    AirtableConfigError,
    AirtableRateLimitError,
    AirtableTableError,
)


class FakeTransport:
    def __init__(self, responses: list[tuple[int, dict[str, Any]]]):
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
        timeout_seconds: int,
    ) -> tuple[int, dict[str, Any]]:
        self.requests.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.responses.pop(0)


def agent_execution_fields() -> dict[str, Any]:
    return {
        "ExecutionId": "exec-test",
        "AgentId": "agent",
        "AgentVersion": "0.1.0",
        "WorkflowId": "workflow",
        "RequestedBy": "company-director",
        "Status": "Draft",
        "WorkflowStatus": "completed",
        "CreatedAt": "2026-07-26T00:00:00+00:00",
    }


def test_airtable_config_loads_from_environment_and_normalizes_base_url() -> None:
    config = AirtableConfig.from_environment(
        env={
            "AIRTABLE_TOKEN": "test-token",
            "AIRTABLE_BASE_ID": "https://airtable.com/app123456789/",
        }
    )

    assert config.token == "test-token"
    assert config.base_id == "app123456789"


def test_airtable_config_loads_from_explicit_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.example"
    env_file.write_text(
        "AIRTABLE_TOKEN=file-token\nAIRTABLE_BASE_ID=https://airtable.com/app987/\n",
        encoding="utf-8",
    )

    config = AirtableConfig.from_environment(env={}, env_file=env_file)

    assert config.token == "file-token"
    assert config.base_id == "app987"


def test_airtable_config_blocks_missing_token() -> None:
    try:
        AirtableConfig.from_environment(env={"AIRTABLE_BASE_ID": "app123"})
    except AirtableConfigError as exc:
        assert "AIRTABLE_TOKEN es obligatorio" in str(exc)
    else:
        raise AssertionError("configuracion sin token debio fallar")


def test_airtable_adapter_blocks_unknown_table(tmp_path: Path) -> None:
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="test-token", base_id="app123"),
        root=tmp_path,
        transport=FakeTransport([]),
    )

    try:
        adapter.list_records("Unknown")
    except AirtableTableError as exc:
        assert "tabla Airtable no permitida" in str(exc)
    else:
        raise AssertionError("tabla desconocida debio fallar")


def test_airtable_adapter_validates_metadata_access(tmp_path: Path) -> None:
    transport = FakeTransport(
        [
            (
                200,
                {
                    "tables": [
                        {"id": "tbl1", "name": "Approvals"},
                        {"id": "tbl2", "name": "Artifacts"},
                    ]
                },
            )
        ]
    )
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="test-token", base_id="app123"),
        root=tmp_path,
        transport=transport,
    )

    result = adapter.validate_access()

    assert result["status"] == "passed"
    assert result["mode"] == "metadata"
    assert result["tables_count"] == 2
    assert result["tables"] == ["Approvals", "Artifacts"]
    assert transport.requests[0]["url"].endswith("/meta/bases/app123/tables")


def test_airtable_adapter_validates_table_access(tmp_path: Path) -> None:
    transport = FakeTransport([(200, {"records": [{"id": "rec123"}]})])
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="test-token", base_id="app123"),
        root=tmp_path,
        transport=transport,
    )

    result = adapter.validate_access(table="Artifacts")

    assert result["status"] == "passed"
    assert result["mode"] == "table"
    assert result["table"] == "Artifacts"
    assert result["records_checked"] == 1
    assert "maxRecords=1" in transport.requests[0]["url"]


def test_airtable_adapter_creates_draft_record(tmp_path: Path) -> None:
    transport = FakeTransport(
        [
            (
                200,
                {
                    "id": "rec123",
                    "fields": {"ExecutionId": "exec-test", "Status": "Draft"},
                },
            )
        ]
    )
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="test-token", base_id="app123"),
        root=tmp_path,
        transport=transport,
    )

    record = adapter.create_draft(
        "AgentExecutions",
        agent_execution_fields(),
    )

    assert record["id"] == "rec123"
    assert transport.requests[0]["method"] == "POST"
    assert transport.requests[0]["body"]["fields"]["Status"] == "Draft"


def test_airtable_adapter_blocks_missing_required_fields(tmp_path: Path) -> None:
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="test-token", base_id="app123"),
        root=tmp_path,
        transport=FakeTransport([]),
    )

    try:
        adapter.create_draft("AgentExecutions", {"ExecutionId": "exec-test"})
    except AirtableTableError as exc:
        assert "faltan campos requeridos" in str(exc)
    else:
        raise AssertionError("draft sin campos requeridos debio fallar")


def test_airtable_adapter_returns_existing_record_for_idempotency(
    tmp_path: Path,
) -> None:
    transport = FakeTransport(
        [
            (
                200,
                {
                    "records": [
                        {
                            "id": "rec-existing",
                            "fields": {"IdempotencyKey": "exec-test"},
                        }
                    ]
                },
            )
        ]
    )
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="test-token", base_id="app123"),
        root=tmp_path,
        transport=transport,
    )

    record = adapter.create_draft(
        "AgentExecutions",
        agent_execution_fields(),
        idempotency_key="exec-test",
    )

    assert record["id"] == "rec-existing"
    assert len(transport.requests) == 1
    assert "filterByFormula" in transport.requests[0]["url"]


def test_airtable_adapter_updates_draft_record(tmp_path: Path) -> None:
    transport = FakeTransport(
        [(200, {"id": "rec123", "fields": {"Status": "Draft"}})]
    )
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="test-token", base_id="app123"),
        root=tmp_path,
        transport=transport,
    )

    record = adapter.update_draft(
        "Approvals",
        "rec123",
        {"Status": "Draft", "Decision": "approved"},
    )

    assert record["id"] == "rec123"
    assert transport.requests[0]["method"] == "PATCH"
    assert transport.requests[0]["url"].endswith("/Approvals/rec123")


def test_airtable_adapter_retries_rate_limit(tmp_path: Path) -> None:
    transport = FakeTransport(
        [
            (429, {"error": {"message": "rate limited"}}),
            (200, {"records": []}),
        ]
    )
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="test-token", base_id="app123", max_retries=1),
        root=tmp_path,
        transport=transport,
    )

    records = adapter.list_records("Artifacts")

    assert records == []
    assert len(transport.requests) == 2


def test_airtable_adapter_raises_after_rate_limit_retries(tmp_path: Path) -> None:
    transport = FakeTransport([(429, {"error": {"message": "rate limited"}})])
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="test-token", base_id="app123", max_retries=0),
        root=tmp_path,
        transport=transport,
    )

    try:
        adapter.list_records("Artifacts")
    except AirtableRateLimitError as exc:
        assert "rate limit agotado" in str(exc)
    else:
        raise AssertionError("rate limit agotado debio fallar")


def test_airtable_audit_log_does_not_store_authorization_token(tmp_path: Path) -> None:
    transport = FakeTransport([(200, {"records": []})])
    adapter = AirtableHttpAdapter(
        config=AirtableConfig(token="secret-token", base_id="app123"),
        root=tmp_path,
        transport=transport,
    )

    adapter.list_records("Artifacts")

    body = (tmp_path / "runtime/data/audit.jsonl").read_text(encoding="utf-8")
    event = json.loads(body)
    assert "secret-token" not in body
    assert event["event_type"] == "airtable.record.read"
