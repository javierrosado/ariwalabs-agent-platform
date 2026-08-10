from pathlib import Path
from typing import Any

from .audit import AuditLogger
from .config import load_yaml
from .handoff_registry import HandoffRegistry
from .skill_registry import SkillRegistry

Finding = dict[str, str]


class FrameworkValidator:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.audit = AuditLogger(self.root / "runtime/data/audit.jsonl")

    def validate_repository(self) -> dict[str, Any]:
        self.audit.validation(
            "framework.validation.started",
            target="repository",
            status="started",
            findings_count=0,
            errors_count=0,
        )
        findings: list[Finding] = []
        agents_dir = self.root / "agents"
        if not agents_dir.exists():
            findings.append(self._finding("error", "No existe agents/"))
        else:
            for agent_dir in sorted(p for p in agents_dir.iterdir() if p.is_dir()):
                findings.extend(self._validate_agent(agent_dir))
            findings.extend(SkillRegistry(self.root).validate_repository())
            findings.extend(HandoffRegistry(self.root).validate_repository())
        status = (
            "blocked"
            if any(finding["severity"] == "error" for finding in findings)
            else ("passed_with_warnings" if findings else "passed")
        )
        errors_count = sum(1 for finding in findings if finding["severity"] == "error")
        self.audit.validation(
            "framework.validation.completed",
            target="repository",
            status=status,
            findings_count=len(findings),
            errors_count=errors_count,
        )
        return {"status": status, "findings": findings}

    def _validate_agent(self, agent_dir: Path) -> list[Finding]:
        findings: list[Finding] = []
        config_path = agent_dir / "agent.yaml"
        if not config_path.exists():
            return [self._finding("error", f"{agent_dir.name}: falta agent.yaml")]
        config = load_yaml(config_path).get("agent", {})
        required = ["id", "name", "version", "purpose", "owner", "autonomy"]
        for field in required:
            if not config.get(field):
                findings.append(self._finding("error", f"{agent_dir.name}: falta {field}"))
        for rel in config.get("shared_context", []):
            if not (self.root / rel).exists():
                findings.append(
                    self._finding("error", f"{agent_dir.name}: contexto inexistente {rel}")
                )
        skills_dir = agent_dir / "skills"
        for skill in config.get("skills", []):
            skill_path = skills_dir / skill / "skill.yaml"
            if not skill_path.exists():
                findings.append(
                    self._finding("error", f"{agent_dir.name}: skill no encontrada {skill}")
                )
        workflow_dir = agent_dir / "workflows"
        for workflow in config.get("workflows", []):
            if not (workflow_dir / f"{workflow}.yaml").exists():
                findings.append(
                    self._finding(
                        "error",
                        f"{agent_dir.name}: workflow no encontrado {workflow}",
                    )
                )
        return findings

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}
