import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .business_packs import BusinessPackRegistry
from .config import load_yaml
from .schema_validator import CoreSchemaValidator

Finding = dict[str, str]

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
KNOWN_EXTERNAL_CONSUMERS = {
    "company-director",
    "registered-agent",
    "content-agent",
    "corporate-opportunity-agent",
    "sales-proposal-agent",
    "student-success-agent",
    "training-program-agent",
}
SENSITIVE_TERMS = {
    "approval",
    "bootcamp",
    "budget",
    "campaign",
    "contact",
    "message",
    "opportunity",
    "publication",
    "proposal",
    "release",
}


@dataclass(frozen=True)
class HandoffRecord:
    handoff_id: str
    version: str
    producer: str
    consumer: str
    trigger: str
    input_required: tuple[str, ...]
    output_required: tuple[str, ...]
    preconditions: tuple[str, ...]
    approval_required: bool
    approval_approver: str
    approval_checkpoint: str
    persistence_current: str
    persistence_future: str
    errors: tuple[str, ...]
    idempotency_key_strategy: str
    path: Path


class HandoffRegistry:
    def __init__(self, root: Path, *, business_pack_id: str | None = None):
        self.root = root.resolve()
        self.business_pack_id = business_pack_id
        self.business_packs = BusinessPackRegistry(self.root)
        self.schema_validator = CoreSchemaValidator(self.root)

    def validate_repository(self) -> list[Finding]:
        findings: list[Finding] = []
        handoff_files = self.business_packs.handoff_files(self.business_pack_id)
        if not handoff_files:
            if self.business_pack_id is not None:
                return []
            return [
                self._finding("error", "docs/handoffs: directorio de handoffs inexistente")
            ]

        records: list[HandoffRecord] = []
        seen_ids: dict[str, Path] = {}
        for path in handoff_files:
            load_findings, file_records = self._load_handoff_file(path)
            findings.extend(load_findings)
            for record in file_records:
                if record.handoff_id in seen_ids:
                    findings.append(
                        self._finding(
                            "error",
                            self._format(
                                path,
                                f"id duplicado {record.handoff_id}; ya existe en "
                                f"{seen_ids[record.handoff_id].relative_to(self.root)}",
                            ),
                        )
                    )
                else:
                    seen_ids[record.handoff_id] = path
                records.append(record)

        if not records:
            findings.append(self._finding("error", "docs/handoffs: no hay handoffs YAML"))

        agent_ids = self._agent_ids()
        for record in records:
            findings.extend(self._validate_record(record, agent_ids))
        return findings

    def list_handoffs(self) -> list[HandoffRecord]:
        records: list[HandoffRecord] = []
        for path in self.business_packs.handoff_files(self.business_pack_id):
            findings, file_records = self._load_handoff_file(path)
            if findings:
                messages = "; ".join(finding["message"] for finding in findings)
                msg = f"handoffs invalidos: {messages}"
                raise ValueError(msg)
            records.extend(file_records)
        return records

    def get_handoff(self, handoff_id: str) -> HandoffRecord:
        for record in self.list_handoffs():
            if record.handoff_id == handoff_id:
                return record
        msg = f"handoff inexistente {handoff_id}"
        raise KeyError(msg)

    def _load_handoff_file(self, path: Path) -> tuple[list[Finding], list[HandoffRecord]]:
        findings: list[Finding] = []
        payload = load_yaml(path)
        findings.extend(
            self.schema_validator.validate_payload(
                payload=payload,
                schema_name="handoff.schema.json",
                source_path=path,
            )
        )
        raw_handoffs = payload.get("handoffs")
        if not isinstance(raw_handoffs, list):
            return [
                self._finding("error", self._format(path, "handoffs debe ser lista"))
            ], []

        records: list[HandoffRecord] = []
        for index, raw_handoff in enumerate(raw_handoffs):
            label = f"handoffs[{index}]"
            record_findings, record = self._load_handoff(path, label, raw_handoff)
            findings.extend(record_findings)
            if record is not None:
                records.append(record)
        return findings, records

    def _load_handoff(
        self,
        path: Path,
        label: str,
        raw_handoff: Any,
    ) -> tuple[list[Finding], HandoffRecord | None]:
        findings: list[Finding] = []
        if not isinstance(raw_handoff, dict):
            return [
                self._finding("error", self._format(path, f"{label}: debe ser objeto"))
            ], None

        required = [
            "id",
            "version",
            "producer",
            "consumer",
            "trigger",
            "input",
            "output",
            "preconditions",
            "approval",
            "persistence",
            "errors",
            "idempotency",
        ]
        for field in required:
            if field not in raw_handoff:
                findings.append(
                    self._finding("error", self._format(path, f"{label}: falta {field}"))
                )

        input_required = self._required_string_list(path, label, raw_handoff, "input")
        output_required = self._required_string_list(path, label, raw_handoff, "output")
        preconditions = self._string_list(
            path,
            label,
            raw_handoff.get("preconditions"),
            "preconditions",
        )
        errors = self._string_list(path, label, raw_handoff.get("errors"), "errors")
        approval = raw_handoff.get("approval", {})
        persistence = raw_handoff.get("persistence", {})
        idempotency = raw_handoff.get("idempotency", {})

        if not isinstance(approval, dict):
            findings.append(
                self._finding("error", self._format(path, f"{label}: approval debe ser objeto"))
            )
            approval = {}
        if not isinstance(persistence, dict):
            findings.append(
                self._finding(
                    "error",
                    self._format(path, f"{label}: persistence debe ser objeto"),
                )
            )
            persistence = {}
        if not isinstance(idempotency, dict):
            findings.append(
                self._finding(
                    "error",
                    self._format(path, f"{label}: idempotency debe ser objeto"),
                )
            )
            idempotency = {}

        handoff_id = self._string_field(path, label, raw_handoff, "id", findings)
        version = self._string_field(path, label, raw_handoff, "version", findings)
        producer = self._string_field(path, label, raw_handoff, "producer", findings)
        consumer = self._string_field(path, label, raw_handoff, "consumer", findings)
        trigger = self._string_field(path, label, raw_handoff, "trigger", findings)
        approval_required = approval.get("required")
        if not isinstance(approval_required, bool):
            findings.append(
                self._finding(
                    "error",
                    self._format(path, f"{label}: approval.required debe ser boolean"),
                )
            )
            approval_required = False
        approval_approver = self._string_field(path, label, approval, "approver", findings)
        approval_checkpoint = self._string_field(path, label, approval, "checkpoint", findings)
        persistence_current = self._string_field(path, label, persistence, "current", findings)
        persistence_future = self._string_field(path, label, persistence, "future", findings)
        idempotency_key_strategy = self._string_field(
            path,
            label,
            idempotency,
            "key_strategy",
            findings,
        )

        if findings:
            return findings, None

        return findings, HandoffRecord(
            handoff_id=handoff_id,
            version=version,
            producer=producer,
            consumer=consumer,
            trigger=trigger,
            input_required=tuple(input_required),
            output_required=tuple(output_required),
            preconditions=tuple(preconditions),
            approval_required=approval_required,
            approval_approver=approval_approver,
            approval_checkpoint=approval_checkpoint,
            persistence_current=persistence_current,
            persistence_future=persistence_future,
            errors=tuple(errors),
            idempotency_key_strategy=idempotency_key_strategy,
            path=path,
        )

    def _validate_record(self, record: HandoffRecord, agent_ids: set[str]) -> list[Finding]:
        findings: list[Finding] = []
        if not VERSION_PATTERN.match(record.version):
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"{record.handoff_id}: version debe usar N.N.N"),
                )
            )
        if record.producer not in agent_ids and record.producer not in KNOWN_EXTERNAL_CONSUMERS:
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"{record.handoff_id}: producer desconocido"),
                )
            )
        if record.consumer not in agent_ids and record.consumer not in KNOWN_EXTERNAL_CONSUMERS:
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"{record.handoff_id}: consumer desconocido"),
                )
            )
        if not record.input_required:
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"{record.handoff_id}: input.required vacio"),
                )
            )
        if not record.output_required:
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"{record.handoff_id}: output.required vacio"),
                )
            )
        if not record.preconditions:
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"{record.handoff_id}: preconditions vacio"),
                )
            )
        if not record.errors:
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"{record.handoff_id}: errors vacio"),
                )
            )
        if not record.idempotency_key_strategy:
            findings.append(
                self._finding(
                    "error",
                    self._format(
                        record.path,
                        f"{record.handoff_id}: idempotency.key_strategy vacio",
                    ),
                )
            )
        uses_sqlite = (
            "sqlite" in record.persistence_current.lower()
            or "sqlite" in record.persistence_future.lower()
        )
        if uses_sqlite:
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"{record.handoff_id}: no usar SQLite"),
                )
            )
        if record.approval_required and record.approval_approver != "company-director":
            findings.append(
                self._finding(
                    "error",
                    self._format(
                        record.path,
                        f"{record.handoff_id}: approver debe ser company-director",
                    ),
                )
            )
        if self._is_sensitive(record) and not record.approval_required:
            findings.append(
                self._finding(
                    "error",
                    self._format(
                        record.path,
                        f"{record.handoff_id}: requiere aprobacion humana",
                    ),
                )
            )
        preconditions_text = " ".join(record.preconditions)
        if (
            record.consumer == "corporate-opportunity-agent"
            and "approval" not in preconditions_text
        ):
            findings.append(
                self._finding(
                    "error",
                    self._format(
                        record.path,
                        f"{record.handoff_id}: oportunidad corporativa requiere aprobacion previa",
                    ),
                )
            )
        return findings

    def _is_sensitive(self, record: HandoffRecord) -> bool:
        text = " ".join(
            (
                record.handoff_id,
                record.trigger,
                record.approval_checkpoint,
                " ".join(record.input_required),
                " ".join(record.output_required),
                " ".join(record.preconditions),
            )
        ).lower()
        return any(term in text for term in SENSITIVE_TERMS)

    def _required_string_list(
        self,
        path: Path,
        label: str,
        payload: dict[str, Any],
        field: str,
    ) -> list[str]:
        value = payload.get(field, {})
        if not isinstance(value, dict):
            return []
        return self._string_list(path, label, value.get("required"), f"{field}.required")

    def _string_list(self, path: Path, label: str, value: Any, field: str) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    def _string_field(
        self,
        path: Path,
        label: str,
        payload: dict[str, Any],
        field: str,
        findings: list[Finding],
    ) -> str:
        value = payload.get(field)
        if not isinstance(value, str):
            findings.append(
                self._finding("error", self._format(path, f"{label}: {field} debe ser string"))
            )
            return ""
        return value

    def _agent_ids(self) -> set[str]:
        ids: set[str] = set()
        for agent_dir in self.business_packs.agent_dirs(self.business_pack_id):
            agent_yaml = agent_dir / "agent.yaml"
            agent_config = load_yaml(agent_yaml).get("agent", {})
            agent_id = agent_config.get("id")
            if isinstance(agent_id, str):
                ids.add(agent_id)
        return ids

    def _format(self, path: Path, message: str) -> str:
        return f"{path.relative_to(self.root)}: {message}"

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}
