from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .audit import AuditLogger
from .config import load_yaml
from .repository import JsonRepository


class AgentRuntime:
    def __init__(self, root: Path):
        self.root = root
        self.repo = JsonRepository(root / "runtime/data")
        self.audit = AuditLogger(root / "runtime/data/audit.jsonl")

    def run(self, request: dict[str, Any]) -> dict[str, Any]:
        agent_id = request["agent_id"]
        agent_path = self.root / "agents" / agent_id
        config = load_yaml(agent_path / "agent.yaml")["agent"]
        workflow_id = request["workflow_id"]
        workflow = load_yaml(agent_path / "workflows" / f"{workflow_id}.yaml")
        execution_id = f"exec-{uuid4().hex[:12]}"
        result = {
            "execution_id": execution_id,
            "agent_id": agent_id,
            "agent_version": config["version"],
            "workflow_id": workflow_id,
            "requested_by": request["requested_by"],
            "created_at": datetime.now(UTC).isoformat(),
            "status": "pending_human_approval",
            "input": request.get("input", {}),
            "workflow_definition": workflow,
            "shared_context": config.get("shared_context", []),
            "approval": {
                "required": True,
                "status": "pending",
                "approver": "company-director",
            },
        }
        path = self.repo.save("executions", execution_id, result)
        self.audit.append("agent.execution.created", {
            "execution_id": execution_id,
            "agent_id": agent_id,
            "workflow_id": workflow_id,
        })
        result["persistence_path"] = str(path.relative_to(self.root))
        return result
