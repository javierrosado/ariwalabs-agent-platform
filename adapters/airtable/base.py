from typing import Any, Protocol

AirtableRecord = dict[str, Any]


class AirtableAdapter(Protocol):
    def validate_access(self, *, table: str | None = None) -> AirtableRecord:
        ...

    def list_records(self, table: str, **filters: Any) -> list[AirtableRecord]:
        ...

    def create_draft(
        self,
        table: str,
        fields: dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> AirtableRecord:
        ...

    def update_draft(
        self,
        table: str,
        record_id: str,
        fields: dict[str, Any],
    ) -> AirtableRecord:
        ...
