from pathlib import Path
from typing import Any

from .agent_registry import AgentRegistry
from .audit import AuditLogger
from .business_packs import BusinessPackRegistry
from .evaluation_engine import EvaluationEngine
from .handoff_registry import HandoffRegistry
from .skill_registry import SkillRegistry

Finding = dict[str, str]


class FrameworkValidator:
    def __init__(self, root: Path, *, business_pack_id: str | None = None):
        self.root = root.resolve()
        self.business_pack_id = business_pack_id
        self.business_packs = BusinessPackRegistry(self.root)
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
        agent_dirs = self.business_packs.agent_dirs(self.business_pack_id)
        if not agent_dirs:
            findings.append(self._finding("error", "No existe agents/"))
        else:
            findings.extend(
                AgentRegistry(
                    self.root,
                    business_pack_id=self.business_pack_id,
                ).validate_repository()
            )
            findings.extend(
                SkillRegistry(
                    self.root,
                    business_pack_id=self.business_pack_id,
                ).validate_repository()
            )
            findings.extend(
                HandoffRegistry(
                    self.root,
                    business_pack_id=self.business_pack_id,
                ).validate_repository()
            )
            findings.extend(
                EvaluationEngine(
                    self.root,
                    business_pack_id=self.business_pack_id,
                ).validate_repository()
            )
        findings.extend(self.business_packs.validate_repository())
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

    def _finding(self, severity: str, message: str) -> Finding:
        return {"severity": severity, "message": message}
