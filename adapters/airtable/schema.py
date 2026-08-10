from dataclasses import dataclass

from .errors import AirtableTableError


@dataclass(frozen=True)
class AirtableTable:
    name: str
    required_fields: tuple[str, ...]
    draft_status_field: str = "Status"
    draft_status_value: str = "Draft"
    idempotency_field: str = "IdempotencyKey"
    privacy_fields: tuple[str, ...] = ()
    approval_fields: tuple[str, ...] = ()


AIRTABLE_TABLES = {
    "Approvals": AirtableTable(
        name="Approvals",
        required_fields=(
            "ApprovalId",
            "ExecutionId",
            "AgentId",
            "WorkflowId",
            "Checkpoint",
            "Approver",
            "Status",
            "CreatedAt",
        ),
        approval_fields=("Approver", "Decision", "DecidedBy"),
    ),
    "AgentExecutions": AirtableTable(
        name="AgentExecutions",
        required_fields=(
            "ExecutionId",
            "AgentId",
            "AgentVersion",
            "WorkflowId",
            "RequestedBy",
            "Status",
            "WorkflowStatus",
            "CreatedAt",
        ),
    ),
    "Artifacts": AirtableTable(
        name="Artifacts",
        required_fields=(
            "ArtifactId",
            "ExecutionId",
            "AgentId",
            "WorkflowId",
            "ArtifactType",
            "SourceAction",
            "Status",
            "Version",
            "CreatedAt",
        ),
    ),
    "Campaigns": AirtableTable(
        name="Campaigns",
        required_fields=("CampaignId", "Objective", "PrioritySegment", "Status"),
        approval_fields=("Approval",),
    ),
    "Cohorts": AirtableTable(
        name="Cohorts",
        required_fields=("CohortId", "TrainingProgram", "Name", "Modality", "Status"),
    ),
    "ContentItems": AirtableTable(
        name="ContentItems",
        required_fields=(
            "ContentItemId",
            "Channel",
            "Format",
            "MessageSummary",
            "CallToAction",
            "Status",
        ),
        approval_fields=("Approval",),
    ),
    "Enrollments": AirtableTable(
        name="Enrollments",
        required_fields=(
            "EnrollmentId",
            "Person",
            "Cohort",
            "TrainingProgram",
            "EnrollmentStatus",
            "ConsentStatus",
            "Status",
        ),
        privacy_fields=("ConsentStatus",),
    ),
    "Events": AirtableTable(
        name="Events",
        required_fields=("EventId", "EventType", "Status"),
    ),
    "Opportunities": AirtableTable(
        name="Opportunities",
        required_fields=(
            "OpportunityId",
            "Organization",
            "SignalSummary",
            "EvidenceSummary",
            "Hypothesis",
            "Confidence",
            "Approval",
            "ContactRestrictions",
            "Status",
        ),
        privacy_fields=("ContactRestrictions",),
        approval_fields=("Approval",),
    ),
    "Organizations": AirtableTable(
        name="Organizations",
        required_fields=(
            "OrganizationId",
            "Name",
            "Source",
            "AuthorizedContactStatus",
            "Status",
        ),
        privacy_fields=("Source", "AuthorizedContactStatus"),
    ),
    "People": AirtableTable(
        name="People",
        required_fields=(
            "PersonId",
            "FullName",
            "Segment",
            "LifecycleStage",
            "ConsentStatus",
            "Status",
        ),
        privacy_fields=("ConsentStatus",),
    ),
    "Referrals": AirtableTable(
        name="Referrals",
        required_fields=(
            "ReferralId",
            "ReferrerPerson",
            "ReferralStatus",
            "ConsentStatus",
            "Status",
        ),
        privacy_fields=("ConsentStatus",),
    ),
    "TrainingPrograms": AirtableTable(
        name="TrainingPrograms",
        required_fields=(
            "TrainingProgramId",
            "Name",
            "Level",
            "MaxHours",
            "Modality",
            "PricePen",
            "CertificateIncluded",
            "Status",
        ),
        approval_fields=("Approval",),
    ),
}


def get_table_contract(table: str) -> AirtableTable:
    try:
        return AIRTABLE_TABLES[table]
    except KeyError as exc:
        msg = f"tabla Airtable no permitida: {table}"
        raise AirtableTableError(msg) from exc
