from pathlib import Path
from ariwalabs.runtime import AgentRuntime

def test_growth_campaign_creates_execution() -> None:
    root = Path(__file__).resolve().parents[2]
    runtime = AgentRuntime(root)
    result = runtime.run({
        "agent_id": "growth-marketing-agent",
        "workflow_id": "create-training-campaign",
        "requested_by": "company-director",
        "input": {"objective": "Test campaign"},
    })
    assert result["status"] == "pending_human_approval"
    assert result["agent_id"] == "growth-marketing-agent"
