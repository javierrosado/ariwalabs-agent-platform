import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .business_packs import BusinessPackRegistry
from .config import load_yaml
from .context_engine import ContextEngine

Finding = dict[str, str]

VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
DEFAULT_OWNER_ROLE = "company-director"
RELEASE_STATUSES = {
    "draft",
    "validated",
    "pending_approval",
    "approved",
    "released",
    "deprecated",
    "blocked",
}


@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    name: str
    version: str
    domain: str
    owner: str
    autonomy: str
    purpose: str
    business_pack_id: str | None
    path: Path
    shared_context: tuple[str, ...]
    policies: tuple[str, ...]
    skills: tuple[str, ...]
    workflows: tuple[str, ...]
    handoffs_produced: tuple[str, ...]
    handoffs_consumed: tuple[str, ...]
    evaluation_rubrics_path: str | None
    release_status: str

    def to_dict(self, root: Path) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "owner": self.owner,
            "autonomy": self.autonomy,
            "purpose": self.purpose,
            "business_pack_id": self.business_pack_id,
            "path": self.path.relative_to(root).as_posix(),
            "shared_context": self.shared_context,
            "policies": self.policies,
            "skills": self.skills,
            "workflows": self.workflows,
            "handoffs_produced": self.handoffs_produced,
            "handoffs_consumed": self.handoffs_consumed,
            "evaluation_rubrics_path": self.evaluation_rubrics_path,
            "release_status": self.release_status,
        }


class AgentRegistry:
    def __init__(self, root: Path, *, business_pack_id: str | None = None):
        self.root = root.resolve()
        self.business_pack_id = business_pack_id
        self.business_packs = BusinessPackRegistry(self.root)

    def list_agents(self) -> list[dict[str, Any]]:
        return [record.to_dict(self.root) for record in self._records()]

    def get_agent(self, agent_id: str) -> dict[str, Any]:
        for record in self._records():
            if record.agent_id == agent_id:
                return record.to_dict(self.root)
        msg = f"agente no registrado {agent_id}"
        raise ValueError(msg)

    def validate_repository(self) -> list[Finding]:
        findings: list[Finding] = []
        records = self._records_with_findings(findings)
        seen_ids: dict[str, Path] = {}
        owner_role = self._owner_role()
        for record in records:
            if record.agent_id in seen_ids:
                findings.append(
                    self._finding(
                        "error",
                        self._format(
                            record.path / "agent.yaml",
                            f"id duplicado {record.agent_id}; ya existe en "
                            f"{seen_ids[record.agent_id].relative_to(self.root).as_posix()}",
                        ),
                    )
                )
            else:
                seen_ids[record.agent_id] = record.path / "agent.yaml"
            findings.extend(self._validate_record(record, owner_role=owner_role))
        return findings

    def _records(self) -> list[AgentRecord]:
        findings: list[Finding] = []
        records = self._records_with_findings(findings)
        if findings:
            messages = "; ".join(finding["message"] for finding in findings)
            raise ValueError(messages)
        return records

    def _records_with_findings(self, findings: list[Finding]) -> list[AgentRecord]:
        records: list[AgentRecord] = []
        handoffs = self._handoffs_by_agent()
        agent_dirs = self.business_packs.agent_dirs(self.business_pack_id)
        if not agent_dirs:
            label = (
                f"business pack {self.business_pack_id}"
                if self.business_pack_id is not None
                else "agents/"
            )
            findings.append(self._finding("error", f"{label}: no hay agentes registrados"))
            return records
        for agent_dir in agent_dirs:
            record = self._load_agent_record(agent_dir, handoffs, findings)
            if record is not None:
                records.append(record)
        return records

    def _load_agent_record(
        self,
        agent_dir: Path,
        handoffs: dict[str, dict[str, set[str]]],
        findings: list[Finding],
    ) -> AgentRecord | None:
        config_path = agent_dir / "agent.yaml"
        if not config_path.exists():
            findings.append(self._finding("error", f"{agent_dir.name}: falta agent.yaml"))
            return None
        agent = load_yaml(config_path).get("agent")
        if not isinstance(agent, dict):
            findings.append(self._finding("error", self._format(config_path, "falta seccion agent")))
            return None
        agent_id = self._string(agent.get("id"), agent_dir.name)
        shared_context = self._strings(agent.get("shared_context", []))
        release_status = self._string(agent.get("release_status"), "draft")
        produced = handoffs.get(agent_id, {}).get("produced", set())
        consumed = handoffs.get(agent_id, {}).get("consumed", set())
        rubrics_path = agent_dir / "evaluations" / "rubrics.yaml"
        return AgentRecord(
            agent_id=agent_id,
            name=self._string(agent.get("name"), ""),
            version=self._string(agent.get("version"), ""),
            domain=self._string(agent.get("domain"), ""),
            owner=self._string(agent.get("owner"), ""),
            autonomy=self._string(agent.get("autonomy"), ""),
            purpose=self._string(agent.get("purpose"), ""),
            business_pack_id=self.business_pack_id,
            path=agent_dir,
            shared_context=tuple(shared_context),
            policies=tuple(path for path in shared_context if "/policies/" in path),
            skills=tuple(self._strings(agent.get("skills", []))),
            workflows=tuple(self._strings(agent.get("workflows", []))),
            handoffs_produced=tuple(sorted(produced)),
            handoffs_consumed=tuple(sorted(consumed)),
            evaluation_rubrics_path=(
                rubrics_path.relative_to(self.root).as_posix() if rubrics_path.exists() else None
            ),
            release_status=release_status,
        )

    def _validate_record(self, record: AgentRecord, *, owner_role: str) -> list[Finding]:
        findings: list[Finding] = []
        config_path = record.path / "agent.yaml"
        required_values = {
            "id": record.agent_id,
            "name": record.name,
            "version": record.version,
            "purpose": record.purpose,
            "owner": record.owner,
            "autonomy": record.autonomy,
        }
        for field, value in required_values.items():
            if not value:
                findings.append(self._finding("error", self._format(config_path, f"falta {field}")))
        if record.agent_id != record.path.name:
            findings.append(
                self._finding(
                    "error",
                    self._format(config_path, f"id debe coincidir con carpeta {record.path.name}"),
                )
            )
        if record.version and not VERSION_PATTERN.match(record.version):
            findings.append(
                self._finding("error", self._format(config_path, "version debe usar formato N.N.N"))
            )
        if record.owner != owner_role:
            findings.append(
                self._finding(
                    "error",
                    self._format(config_path, f"owner debe ser {owner_role}"),
                )
            )
        if record.release_status not in RELEASE_STATUSES:
            findings.append(
                self._finding(
                    "error",
                    self._format(config_path, f"release_status invalido {record.release_status}"),
                )
            )
        findings.extend(self._validate_declared_files(record))
        findings.extend(
            ContextEngine(
                self.root,
                business_pack_id=self.business_pack_id,
            ).validate_agent_context(
                agent_id=record.agent_id,
                agent_config=load_yaml(config_path).get("agent", {}),
            )
        )
        findings.extend(self._validate_release_governance(record))
        return findings

    def _validate_declared_files(self, record: AgentRecord) -> list[Finding]:
        findings: list[Finding] = []
        for skill in record.skills:
            if not (record.path / "skills" / skill / "skill.yaml").exists():
                findings.append(
                    self._finding("error", self._format(record.path, f"skill no encontrada {skill}"))
                )
        for workflow in record.workflows:
            if not (record.path / "workflows" / f"{workflow}.yaml").exists():
                findings.append(
                    self._finding(
                        "error",
                        self._format(record.path, f"workflow no encontrado {workflow}"),
                    )
                )
        if record.skills and record.evaluation_rubrics_path is None:
            findings.append(
                self._finding("error", self._format(record.path, "falta evaluations/rubrics.yaml"))
            )
        return findings

    def _validate_release_governance(self, record: AgentRecord) -> list[Finding]:
        if record.release_status in {"approved", "released"}:
            approval_path = record.path / "release-approval.yaml"
            if not approval_path.exists():
                return [
                    self._finding(
                        "error",
                        self._format(
                            record.path / "agent.yaml",
                            "release aprobado requiere release-approval.yaml",
                        ),
                    )
                ]
        return []

    def _handoffs_by_agent(self) -> dict[str, dict[str, set[str]]]:
        handoffs: dict[str, dict[str, set[str]]] = {}
        for path in self.business_packs.handoff_files(self.business_pack_id):
            payload = load_yaml(path)
            raw_handoffs = payload.get("handoffs", [])
            if not isinstance(raw_handoffs, list):
                continue
            for raw_handoff in raw_handoffs:
                if not isinstance(raw_handoff, dict):
                    continue
                handoff_id = raw_handoff.get("id")
                producer = raw_handoff.get("producer")
                consumer = raw_handoff.get("consumer")
                if not isinstance(handoff_id, str):
                    continue
                if isinstance(producer, str):
                    handoffs.setdefault(producer, {"produced": set(), "consumed": set()})[
                        "produced"
                    ].add(handoff_id)
                if isinstance(consumer, str):
                    handoffs.setdefault(consumer, {"produced": set(), "consumed": set()})[
                        "consumed"
                    ].add(handoff_id)
        return handoffs

    def _owner_role(self) -> str:
        if self.business_pack_id is None:
            return DEFAULT_OWNER_ROLE
        return self.business_packs.load(self.business_pack_id).owner_role or DEFAULT_OWNER_ROLE

    def _strings(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    def _string(self, value: Any, default: str) -> str:
        return value if isinstance(value, str) else default

    def _format(self, path: Path, message: str) -> str:
        return f"{path.relative_to(self.root).as_posix()}: {message}"

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}
