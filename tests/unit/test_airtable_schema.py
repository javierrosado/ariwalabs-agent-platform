from adapters.airtable.schema import AIRTABLE_TABLES

EXPECTED_TABLES = {
    "AgentExecutions",
    "Approvals",
    "Artifacts",
    "Campaigns",
    "Cohorts",
    "ContentItems",
    "Enrollments",
    "Events",
    "Opportunities",
    "Organizations",
    "People",
    "Referrals",
    "TrainingPrograms",
}

PRIVACY_TABLES = {
    "Enrollments",
    "Opportunities",
    "Organizations",
    "People",
    "Referrals",
}

APPROVAL_TABLES = {
    "Approvals",
    "Campaigns",
    "ContentItems",
    "Opportunities",
    "TrainingPrograms",
}


def test_airtable_schema_declares_all_backlog_tables() -> None:
    assert set(AIRTABLE_TABLES) == EXPECTED_TABLES


def test_airtable_schema_requires_status_and_idempotency() -> None:
    for table in AIRTABLE_TABLES.values():
        assert "Status" in table.required_fields
        assert table.idempotency_field == "IdempotencyKey"


def test_airtable_schema_declares_runtime_governance_fields() -> None:
    assert {
        "ExecutionId",
        "AgentId",
        "AgentVersion",
        "WorkflowId",
        "RequestedBy",
        "WorkflowStatus",
        "CreatedAt",
    }.issubset(AIRTABLE_TABLES["AgentExecutions"].required_fields)
    assert {
        "ApprovalId",
        "ExecutionId",
        "Checkpoint",
        "Approver",
        "CreatedAt",
    }.issubset(AIRTABLE_TABLES["Approvals"].required_fields)
    assert {
        "ArtifactId",
        "ExecutionId",
        "ArtifactType",
        "SourceAction",
        "Version",
        "CreatedAt",
    }.issubset(AIRTABLE_TABLES["Artifacts"].required_fields)


def test_airtable_schema_marks_privacy_sensitive_tables() -> None:
    for table_name in PRIVACY_TABLES:
        assert AIRTABLE_TABLES[table_name].privacy_fields


def test_airtable_schema_marks_approval_sensitive_tables() -> None:
    for table_name in APPROVAL_TABLES:
        assert AIRTABLE_TABLES[table_name].approval_fields
