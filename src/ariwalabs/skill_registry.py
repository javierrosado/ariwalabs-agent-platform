import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .business_packs import BusinessPackRegistry
from .config import load_yaml
from .model_profiles import SUPPORTED_MODEL_PROFILES
from .schema_validator import CoreSchemaValidator
from .tool_gateway import ToolGateway

Finding = dict[str, str]

SENSITIVE_SKILL_SLUGS = {
    "bootcamp-planning",
    "campaign-design",
    "corporate-opportunity-detection",
    "referral-program",
}
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class SkillRecord:
    agent_id: str
    agent_owner: str
    agent_approvals: tuple[str, ...]
    slug: str
    skill_id: str
    version: str
    model_profile: str
    path: Path
    output_schema_path: Path
    approval_required: bool
    tools_allowed: tuple[str, ...]
    tools_prohibited: tuple[str, ...]


class SkillRegistry:
    def __init__(self, root: Path, *, business_pack_id: str | None = None):
        self.root = root.resolve()
        self.business_pack_id = business_pack_id
        self.business_packs = BusinessPackRegistry(self.root)
        self.schema_validator = CoreSchemaValidator(self.root)
        self.tool_gateway = ToolGateway(self.root)

    def validate_repository(self) -> list[Finding]:
        findings: list[Finding] = []
        records: list[SkillRecord] = []
        seen_ids: dict[str, Path] = {}
        agent_dirs = self.business_packs.agent_dirs(self.business_pack_id)
        if not agent_dirs:
            return findings

        for agent_dir in agent_dirs:
            agent_config = load_yaml(agent_dir / "agent.yaml").get("agent", {})
            for skill_path in sorted(agent_dir.glob("skills/*/skill.yaml")):
                skill_findings, record = self._load_skill(agent_dir, agent_config, skill_path)
                findings.extend(skill_findings)
                if record is None:
                    continue
                if record.skill_id in seen_ids:
                    findings.append(
                        self._finding(
                            "error",
                            self._format(
                                skill_path,
                                f"id duplicado {record.skill_id}; ya existe en "
                                f"{seen_ids[record.skill_id].relative_to(self.root)}",
                            ),
                        )
                    )
                else:
                    seen_ids[record.skill_id] = skill_path
                records.append(record)

        for record in records:
            findings.extend(self._validate_record(record))
            findings.extend(
                self._validate_output_schema(
                    skill_path=record.path,
                    schema_path=record.output_schema_path,
                )
            )
        return findings

    def _load_skill(
        self,
        agent_dir: Path,
        agent_config: dict[str, Any],
        skill_path: Path,
    ) -> tuple[list[Finding], SkillRecord | None]:
        findings: list[Finding] = []
        raw_payload = load_yaml(skill_path)
        findings.extend(
            self.schema_validator.validate_payload(
                payload=raw_payload,
                schema_name="skill.schema.json",
                source_path=skill_path,
            )
        )
        skill_payload = raw_payload.get("skill")
        if not isinstance(skill_payload, dict):
            return [self._finding("error", self._format(skill_path, "falta seccion skill"))], None

        blocking_findings: list[Finding] = []
        required = [
            "id",
            "version",
            "purpose",
            "model_profile",
            "approval_required",
            "output_schema",
        ]
        for field in required:
            if field not in skill_payload:
                blocking_findings.append(
                    self._finding("error", self._format(skill_path, f"falta {field}"))
                )

        skill_id = skill_payload.get("id")
        version = skill_payload.get("version")
        model_profile = skill_payload.get("model_profile")
        output_schema = skill_payload.get("output_schema")
        approval_required = skill_payload.get("approval_required")
        tools = skill_payload.get("tools", {})
        allowed = self._load_tool_list(skill_path, tools, "allowed", findings)
        prohibited = self._load_tool_list(skill_path, tools, "prohibited", findings)

        if not isinstance(skill_id, str):
            blocking_findings.append(
                self._finding("error", self._format(skill_path, "id debe ser string"))
            )
            skill_id = ""
        if not isinstance(version, str):
            blocking_findings.append(
                self._finding("error", self._format(skill_path, "version debe ser string"))
            )
            version = ""
        if not isinstance(model_profile, str):
            blocking_findings.append(
                self._finding("error", self._format(skill_path, "model_profile debe ser string"))
            )
            model_profile = ""
        if not isinstance(output_schema, str):
            blocking_findings.append(
                self._finding("error", self._format(skill_path, "output_schema debe ser string"))
            )
            output_schema = ""
        if not isinstance(approval_required, bool):
            blocking_findings.append(
                self._finding(
                    "error",
                    self._format(skill_path, "approval_required debe ser boolean"),
                )
            )
            approval_required = False

        findings.extend(blocking_findings)
        if blocking_findings:
            return findings, None

        agent_id = str(agent_config.get("id", agent_dir.name))
        return findings, SkillRecord(
            agent_id=agent_id,
            agent_owner=str(agent_config.get("owner", "")),
            agent_approvals=self._agent_approvals(agent_config),
            slug=skill_path.parent.name,
            skill_id=skill_id,
            version=version,
            model_profile=model_profile,
            path=skill_path,
            output_schema_path=(skill_path.parent / output_schema).resolve(),
            approval_required=approval_required,
            tools_allowed=tuple(allowed),
            tools_prohibited=tuple(prohibited),
        )

    def _load_tool_list(
        self,
        skill_path: Path,
        tools: Any,
        key: str,
        findings: list[Finding],
    ) -> list[str]:
        if tools in ({}, None):
            return []
        if not isinstance(tools, dict):
            findings.append(
                self._finding("error", self._format(skill_path, "tools debe ser objeto"))
            )
            return []
        raw_values = tools.get(key, [])
        if not isinstance(raw_values, list):
            findings.append(
                self._finding("error", self._format(skill_path, f"tools.{key} debe ser lista"))
            )
            return []
        values: list[str] = []
        for value in raw_values:
            if isinstance(value, str):
                values.append(value)
            else:
                findings.append(
                    self._finding(
                        "error",
                        self._format(skill_path, f"tools.{key} contiene valor no string"),
                    )
                )
        return values

    def _validate_record(self, record: SkillRecord) -> list[Finding]:
        findings: list[Finding] = []
        expected_prefix = f"{record.agent_id.removesuffix('-agent')}."
        expected_suffix = f".{record.slug}"

        if record.agent_owner != "company-director":
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, "owner del agente debe ser company-director"),
                )
            )
        if not record.skill_id.startswith(expected_prefix):
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"id debe iniciar con {expected_prefix}"),
                )
            )
        if not record.skill_id.endswith(expected_suffix):
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, f"id debe terminar con {record.slug}"),
                )
            )
        if not VERSION_PATTERN.match(record.version):
            findings.append(
                self._finding("error", self._format(record.path, "version debe usar formato N.N.N"))
            )
        if record.model_profile not in SUPPORTED_MODEL_PROFILES:
            findings.append(
                self._finding(
                    "error",
                    self._format(
                        record.path,
                        f"model_profile no soportado {record.model_profile}",
                    ),
                )
            )

        findings.extend(
            self.tool_gateway.validate_skill_tools(
                skill_path=record.path,
                allowed=record.tools_allowed,
                prohibited=record.tools_prohibited,
            )
        )

        if record.slug in SENSITIVE_SKILL_SLUGS and not record.approval_required:
            findings.append(
                self._finding(
                    "error",
                    self._format(record.path, "skill sensible requiere aprobacion"),
                )
            )
        if record.approval_required and not record.agent_approvals:
            findings.append(
                self._finding(
                    "error",
                    self._format(
                        record.path,
                        "skill con aprobacion requiere approvals en agent.yaml",
                    ),
                )
            )
        return findings

    def _validate_output_schema(self, *, skill_path: Path, schema_path: Path) -> list[Finding]:
        findings: list[Finding] = []
        if not schema_path.exists():
            return [
                self._finding(
                    "error",
                    self._format(
                        skill_path,
                        f"output_schema inexistente {schema_path.relative_to(self.root)}",
                    ),
                )
            ]

        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return [
                self._finding(
                    "error",
                    self._format(skill_path, f"output_schema JSON invalido {exc.msg}"),
                )
            ]

        label = self._format(skill_path, str(schema_path.relative_to(self.root)))
        if not isinstance(schema, dict):
            return [self._finding("error", f"{label}: schema debe ser un objeto JSON")]
        if schema.get("type") != "object":
            findings.append(self._finding("error", f"{label}: type debe ser object"))
        required = schema.get("required")
        if not isinstance(required, list) or not required:
            findings.append(
                self._finding("error", f"{label}: required debe ser una lista no vacia")
            )
            required = []
        properties = schema.get("properties")
        if not isinstance(properties, dict) or not properties:
            findings.append(
                self._finding("error", f"{label}: properties debe ser un objeto no vacio")
            )
            properties = {}
        if schema.get("additionalProperties") is not False:
            findings.append(self._finding("error", f"{label}: additionalProperties debe ser false"))

        for field in required:
            if isinstance(field, str) and field not in properties:
                findings.append(
                    self._finding(
                        "error",
                        f"{label}: required referencia campo inexistente {field}",
                    )
                )

        if "errors" not in properties and "findings" not in properties:
            findings.append(
                self._finding("error", f"{label}: debe definir errors o findings para fallos")
            )

        findings.extend(self._validate_schema_node(label, schema))
        return findings

    def _validate_schema_node(self, label: str, node: Any) -> list[Finding]:
        findings: list[Finding] = []
        if isinstance(node, dict):
            if node.get("additionalProperties") is True:
                findings.append(
                    self._finding("error", f"{label}: additionalProperties true no permitido")
                )
            has_schema_shape = any(
                key in node
                for key in (
                    "type",
                    "enum",
                    "const",
                    "$ref",
                    "anyOf",
                    "oneOf",
                    "allOf",
                    "items",
                    "properties",
                )
            )
            has_type_marker = any(
                key in node
                for key in (
                    "type",
                    "enum",
                    "const",
                    "$ref",
                    "anyOf",
                    "oneOf",
                    "allOf",
                )
            )
            if has_schema_shape and not has_type_marker:
                findings.append(self._finding("error", f"{label}: nodo de schema sin tipo"))
            for child in node.values():
                findings.extend(self._validate_schema_node(label, child))
        elif isinstance(node, list):
            for child in node:
                findings.extend(self._validate_schema_node(label, child))
        return findings

    def _agent_approvals(self, agent_config: dict[str, Any]) -> tuple[str, ...]:
        approvals = agent_config.get("approvals", agent_config.get("approval_required", []))
        if not isinstance(approvals, list):
            return ()
        return tuple(value for value in approvals if isinstance(value, str))

    def _format(self, path: Path, message: str) -> str:
        return f"{path.relative_to(self.root)}: {message}"

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}
