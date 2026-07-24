from typing import Any, Protocol


class AirtableAdapter(Protocol):
    def list_records(self, table: str, **filters: Any) -> list[dict[str, Any]]:
        ...

    def create_draft(self, table: str, fields: dict[str, Any]) -> dict[str, Any]:
        ...

    def update_draft(self, table: str, record_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        ...
