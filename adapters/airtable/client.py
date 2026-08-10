import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from ariwalabs.audit import AuditLogger

from .base import AirtableRecord
from .errors import (
    AirtableConfigError,
    AirtableIdempotencyError,
    AirtableRateLimitError,
    AirtableRemoteError,
    AirtableTableError,
)
from .schema import get_table_contract

AIRTABLE_API_URL = "https://api.airtable.com/v0"
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_MAX_RETRIES = 2
RATE_LIMIT_STATUS = 429


class HttpTransport(Protocol):
    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
        timeout_seconds: int,
    ) -> tuple[int, dict[str, Any]]:
        ...


class UrlLibTransport:
    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
        timeout_seconds: int,
    ) -> tuple[int, dict[str, Any]]:
        encoded_body = None
        if body is not None:
            encoded_body = json.dumps(body).encode("utf-8")
        request = Request(
            url,
            data=encoded_body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8") or "{}")
                return response.status, payload
        except HTTPError as exc:
            payload = json.loads(exc.read().decode("utf-8") or "{}")
            return exc.code, payload
        except URLError as exc:
            msg = f"error de red Airtable: {exc.reason}"
            raise AirtableRemoteError(msg) from exc


@dataclass(frozen=True)
class AirtableConfig:
    token: str
    base_id: str
    api_url: str = AIRTABLE_API_URL
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES

    def __post_init__(self) -> None:
        object.__setattr__(self, "token", self.token.strip())
        object.__setattr__(self, "base_id", _normalize_base_id(self.base_id))

    @classmethod
    def from_environment(
        cls,
        *,
        root: Path | None = None,
        env_file: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> "AirtableConfig":
        values = dict(os.environ if env is None else env)
        config_file = env_file
        if config_file is None and root is not None:
            config_file = root / ".env"
        if config_file is not None:
            values = {**_load_env_file(config_file), **values}
        token = values.get("AIRTABLE_TOKEN", "").strip()
        base_id = _normalize_base_id(values.get("AIRTABLE_BASE_ID", ""))
        if not token:
            msg = "AIRTABLE_TOKEN es obligatorio"
            raise AirtableConfigError(msg)
        if not base_id:
            msg = "AIRTABLE_BASE_ID es obligatorio"
            raise AirtableConfigError(msg)
        return cls(token=token, base_id=base_id)


class AirtableHttpAdapter:
    def __init__(
        self,
        *,
        config: AirtableConfig,
        root: Path | None = None,
        transport: HttpTransport | None = None,
    ):
        self.config = config
        self.transport = transport or UrlLibTransport()
        audit_root = root or Path(".")
        self.audit = AuditLogger(audit_root / "runtime/data/audit.jsonl")

    def validate_access(self, *, table: str | None = None) -> AirtableRecord:
        if table is not None:
            get_table_contract(table)
            payload = self._request("GET", table, query={"maxRecords": "1"})
            records = payload.get("records", [])
            if not isinstance(records, list):
                msg = f"{table}: respuesta Airtable invalida"
                raise AirtableRemoteError(msg)
            result: AirtableRecord = {
                "status": "passed",
                "base_id": self.config.base_id,
                "mode": "table",
                "table": table,
                "records_checked": len(records),
            }
            self.audit.append(
                "airtable.access.validated",
                {"base_id": self.config.base_id, "mode": "table", "table": table},
            )
            return result

        payload = self._request_absolute(
            "GET",
            f"{self.config.api_url}/meta/bases/{quote(self.config.base_id)}/tables",
        )
        tables = payload.get("tables", [])
        if not isinstance(tables, list):
            msg = "respuesta metadata Airtable invalida"
            raise AirtableRemoteError(msg)
        table_names = [
            table_payload["name"]
            for table_payload in tables
            if isinstance(table_payload, dict) and isinstance(table_payload.get("name"), str)
        ]
        result = {
            "status": "passed",
            "base_id": self.config.base_id,
            "mode": "metadata",
            "tables_count": len(tables),
            "tables": table_names,
        }
        self.audit.append(
            "airtable.access.validated",
            {"base_id": self.config.base_id, "mode": "metadata", "tables_count": len(tables)},
        )
        return result

    def list_records(self, table: str, **filters: Any) -> list[AirtableRecord]:
        get_table_contract(table)
        query = self._query(filters)
        payload = self._request("GET", table, query=query)
        records = payload.get("records", [])
        if not isinstance(records, list):
            msg = f"{table}: respuesta Airtable invalida"
            raise AirtableRemoteError(msg)
        self.audit.append(
            "airtable.record.read",
            {"table": table, "filters": sorted(filters), "count": len(records)},
        )
        return records

    def create_draft(
        self,
        table: str,
        fields: dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> AirtableRecord:
        contract = get_table_contract(table)
        draft_fields = {
            **fields,
            contract.draft_status_field: fields.get(
                contract.draft_status_field,
                contract.draft_status_value,
            ),
        }
        missing = [field for field in contract.required_fields if field not in draft_fields]
        if missing:
            msg = f"{table}: faltan campos requeridos {missing}"
            raise AirtableTableError(msg)
        if idempotency_key is not None:
            draft_fields[contract.idempotency_field] = idempotency_key
            existing = self.list_records(
                table,
                **{contract.idempotency_field: idempotency_key},
            )
            if len(existing) > 1:
                msg = f"{table}: idempotency_key duplicada"
                raise AirtableIdempotencyError(msg)
            if existing:
                return existing[0]
        payload = self._request(
            "POST",
            table,
            body={"fields": draft_fields, "typecast": True},
        )
        self.audit.append(
            "airtable.record.created",
            {
                "table": table,
                "record_id": payload.get("id"),
                "field_names": sorted(draft_fields),
                "idempotent": idempotency_key is not None,
            },
        )
        return payload

    def update_draft(
        self,
        table: str,
        record_id: str,
        fields: dict[str, Any],
    ) -> AirtableRecord:
        get_table_contract(table)
        if not record_id.strip():
            msg = "record_id es obligatorio"
            raise ValueError(msg)
        payload = self._request(
            "PATCH",
            table,
            record_id=record_id,
            body={"fields": fields, "typecast": True},
        )
        self.audit.append(
            "airtable.record.updated",
            {
                "table": table,
                "record_id": payload.get("id", record_id),
                "field_names": sorted(fields),
            },
        )
        return payload

    def _request_absolute(
        self,
        method: str,
        url: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._send(method=method, url=url, body=body, audit_table="metadata")

    def _request(
        self,
        method: str,
        table: str,
        *,
        record_id: str | None = None,
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = self._url(table, record_id=record_id, query=query)
        return self._send(method=method, url=url, body=body, audit_table=table)

    def _send(
        self,
        *,
        method: str,
        url: str,
        audit_table: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": "application/json",
        }
        last_payload: dict[str, Any] = {}
        for attempt in range(self.config.max_retries + 1):
            status, payload = self.transport.request(
                method=method,
                url=url,
                headers=headers,
                body=body,
                timeout_seconds=self.config.timeout_seconds,
            )
            if status == RATE_LIMIT_STATUS:
                last_payload = payload
                if attempt >= self.config.max_retries:
                    self.audit.error(
                        "airtable.error",
                        error_type="AirtableRateLimitError",
                        message="rate limit agotado",
                        metadata={"table": audit_table, "method": method},
                    )
                    msg = "rate limit agotado"
                    raise AirtableRateLimitError(msg)
                time.sleep(0.1 * (attempt + 1))
                continue
            if status >= 400:
                message = self._error_message(payload)
                self.audit.error(
                    "airtable.error",
                    error_type="AirtableRemoteError",
                    message=message,
                    metadata={"table": audit_table, "method": method, "status": status},
                )
                raise AirtableRemoteError(message)
            return payload
        msg = self._error_message(last_payload)
        raise AirtableRateLimitError(msg)

    def _url(
        self,
        table: str,
        *,
        record_id: str | None = None,
        query: dict[str, str] | None = None,
    ) -> str:
        path = f"{self.config.api_url}/{self.config.base_id}/{quote(table)}"
        if record_id is not None:
            path = f"{path}/{quote(record_id)}"
        if query:
            return f"{path}?{urlencode(query)}"
        return path

    def _query(self, filters: dict[str, Any]) -> dict[str, str]:
        if not filters:
            return {}
        expressions = []
        for field, value in sorted(filters.items()):
            safe_field = str(field).replace("}", "")
            safe_value = str(value).replace("'", "\\'")
            expressions.append(f"{{{safe_field}}}='{safe_value}'")
        formula = expressions[0] if len(expressions) == 1 else f"AND({','.join(expressions)})"
        return {"filterByFormula": formula}

    def _error_message(self, payload: dict[str, Any]) -> str:
        error = payload.get("error", {})
        if isinstance(error, dict):
            message = error.get("message") or error.get("type")
            if isinstance(message, str):
                return message
        return "error remoto Airtable"


def _normalize_base_id(raw_base_id: str) -> str:
    value = raw_base_id.strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        parsed = urlparse(value)
        parts = [part for part in parsed.path.split("/") if part]
        return parts[0] if parts else ""
    return value


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
