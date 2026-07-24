from pathlib import Path
from typing import Any

from .config import load_yaml


class FrameworkValidator:
    def __init__(self, root: Path):
        self.root = root

    def validate_repository(self) -> dict[str, Any]:
        findings: list[dict[str, str]] = []
        agents_dir = self.root / "agents"
        if not agents_dir.exists():
            findings.append({"severity":"error","message":"No existe agents/"})
        else:
            for agent_dir in sorted(p for p in agents_dir.iterdir() if p.is_dir()):
                findings.extend(self._validate_agent(agent_dir))
        status = "blocked" if any(x["severity"] == "error" for x in findings) else (
            "passed_with_warnings" if findings else "passed"
        )
        return {"status":status,"findings":findings}

    def _validate_agent(self, agent_dir: Path) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        config_path = agent_dir / "agent.yaml"
        if not config_path.exists():
            return [{"severity":"error","message":f"{agent_dir.name}: falta agent.yaml"}]
        config = load_yaml(config_path).get("agent", {})
        required = ["id","name","version","purpose","owner","autonomy"]
        for field in required:
            if not config.get(field):
                findings.append({"severity":"error","message":f"{agent_dir.name}: falta {field}"})
        for rel in config.get("shared_context", []):
            if not (self.root / rel).exists():
                findings.append({"severity":"error","message":f"{agent_dir.name}: contexto inexistente {rel}"})
        skills_dir = agent_dir / "skills"
        for skill in config.get("skills", []):
            if not (skills_dir / skill / "skill.yaml").exists():
                findings.append({"severity":"error","message":f"{agent_dir.name}: skill no encontrada {skill}"})
        workflow_dir = agent_dir / "workflows"
        for workflow in config.get("workflows", []):
            if not (workflow_dir / f"{workflow}.yaml").exists():
                findings.append({"severity":"error","message":f"{agent_dir.name}: workflow no encontrado {workflow}"})
        return findings
