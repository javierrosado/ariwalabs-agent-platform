import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from adapters.airtable.client import AirtableConfig
from adapters.airtable.schema import AIRTABLE_TABLES

API_URL = "https://api.airtable.com/v0"
RATE_LIMIT_STATUS = 429
MAX_RETRIES = 2

STATUS_CHOICES = [
    "Draft",
    "PendingApproval",
    "Approved",
    "Rejected",
    "Active",
    "Archived",
]

WORKFLOW_STATUS_CHOICES = [
    "started",
    "completed",
    "blocked",
    "paused_for_approval",
]

DECISION_CHOICES = ["approved", "rejected"]

LONG_TEXT_FIELDS = {
    "CallToAction",
    "ContactRestrictions",
    "EvidenceSummary",
    "Hypothesis",
    "InputSummary",
    "MessageSummary",
    "MetadataSummary",
    "Notes",
    "Objective",
    "Reason",
    "SignalSummary",
}

CHECKBOX_FIELDS = {"CertificateIncluded"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config = AirtableConfig.from_environment(root=root, env_file=root / args.env_file)
    client = AirtableSchemaClient(config)
    existing_tables = client.list_tables()
    result = {
        "status": "passed",
        "base_id": config.base_id,
        "dry_run": args.dry_run,
        "created_tables": [],
        "updated_tables": [],
        "skipped_tables": [],
    }

    table_ids = {
        table["name"]: table["id"]
        for table in existing_tables
        if isinstance(table.get("name"), str) and isinstance(table.get("id"), str)
    }
    table_fields = {
        table["name"]: {
            field["name"]
            for field in table.get("fields", [])
            if isinstance(field, dict) and isinstance(field.get("name"), str)
        }
        for table in existing_tables
        if isinstance(table.get("name"), str)
    }

    for table_name, contract in AIRTABLE_TABLES.items():
        required_fields = list(dict.fromkeys(contract.required_fields + ("IdempotencyKey",)))
        if table_name not in table_ids:
            if args.dry_run:
                result["created_tables"].append(
                    {"table": table_name, "fields": required_fields}
                )
                continue
            created = client.create_table(table_name, required_fields[0])
            table_ids[table_name] = created["id"]
            table_fields[table_name] = {required_fields[0]}
            result["created_tables"].append({"table": table_name})

        missing_fields = [
            field for field in required_fields if field not in table_fields.get(table_name, set())
        ]
        if missing_fields:
            if args.dry_run:
                result["updated_tables"].append(
                    {"table": table_name, "fields": missing_fields}
                )
                continue
            for field_name in missing_fields:
                client.create_field(
                    table_id=table_ids[table_name],
                    field_name=field_name,
                    field_definition=field_definition(field_name),
                )
                table_fields.setdefault(table_name, set()).add(field_name)
            result["updated_tables"].append(
                {"table": table_name, "fields": missing_fields}
            )
        else:
            result["skipped_tables"].append({"table": table_name})

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


class AirtableSchemaClient:
    def __init__(self, config: AirtableConfig):
        self.config = config

    def list_tables(self) -> list[dict[str, Any]]:
        payload = self.request(
            "GET",
            f"{API_URL}/meta/bases/{quote(self.config.base_id)}/tables",
            body=None,
        )
        tables = payload.get("tables", [])
        if not isinstance(tables, list):
            msg = "respuesta metadata Airtable invalida"
            raise TypeError(msg)
        return tables

    def create_table(self, table_name: str, primary_field: str) -> dict[str, Any]:
        payload = self.request(
            "POST",
            f"{API_URL}/meta/bases/{quote(self.config.base_id)}/tables",
            body={
                "name": table_name,
                "fields": [
                    {
                        "name": primary_field,
                        "type": "singleLineText",
                    }
                ],
            },
        )
        table_id = payload.get("id")
        if not isinstance(table_id, str):
            msg = f"{table_name}: Airtable no devolvio id de tabla"
            raise TypeError(msg)
        return {"id": table_id, "name": table_name}

    def create_field(
        self,
        *,
        table_id: str,
        field_name: str,
        field_definition: dict[str, Any],
    ) -> None:
        self.request(
            "POST",
            f"{API_URL}/meta/bases/{quote(self.config.base_id)}/tables/{table_id}/fields",
            body={"name": field_name, **field_definition},
        )

    def request(
        self,
        method: str,
        url: str,
        *,
        body: dict[str, Any] | None,
    ) -> dict[str, Any]:
        encoded_body = None
        if body is not None:
            encoded_body = json.dumps(body).encode("utf-8")
        request = Request(
            url,
            data=encoded_body,
            method=method,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json",
            },
        )
        for attempt in range(MAX_RETRIES + 1):
            try:
                with urlopen(request, timeout=20) as response:
                    return json.loads(response.read().decode("utf-8") or "{}")
            except HTTPError as exc:
                payload = json.loads(exc.read().decode("utf-8") or "{}")
                if exc.code == RATE_LIMIT_STATUS and attempt < MAX_RETRIES:
                    time.sleep(0.2 * (attempt + 1))
                    continue
                message = error_message(payload)
                msg = f"Airtable {method} fallo: {message}"
                raise RuntimeError(msg) from exc
            except URLError as exc:
                msg = f"error de red Airtable: {exc.reason}"
                raise RuntimeError(msg) from exc
        msg = "rate limit agotado"
        raise RuntimeError(msg)


def field_definition(field_name: str) -> dict[str, Any]:
    if field_name in CHECKBOX_FIELDS:
        return {
            "type": "checkbox",
            "options": {"icon": "check", "color": "greenBright"},
        }
    if field_name in LONG_TEXT_FIELDS:
        return {"type": "multilineText"}
    if field_name == "Status":
        return single_select_definition(STATUS_CHOICES)
    if field_name == "WorkflowStatus":
        return single_select_definition(WORKFLOW_STATUS_CHOICES)
    if field_name == "Decision":
        return single_select_definition(DECISION_CHOICES)
    return {"type": "singleLineText"}


def single_select_definition(choices: list[str]) -> dict[str, Any]:
    return {
        "type": "singleSelect",
        "options": {"choices": [{"name": choice} for choice in choices]},
    }


def error_message(payload: dict[str, Any]) -> str:
    error = payload.get("error", {})
    if isinstance(error, dict):
        message = error.get("message") or error.get("type")
        if isinstance(message, str):
            return message
    return "error remoto Airtable"


if __name__ == "__main__":
    sys.exit(main())
