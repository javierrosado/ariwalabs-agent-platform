from pathlib import Path

from ariwalabs.artifact_manager import ArtifactManager


def test_artifact_manager_creates_and_lists_artifact(tmp_path: Path) -> None:
    manager = ArtifactManager(tmp_path)

    artifact = manager.create(
        execution_id="exec-test",
        agent_id="growth-marketing-agent",
        workflow_id="manage-student-growth-journey",
        artifact_type="journey_state",
        source_action="persist_state",
        status="draft",
        metadata={"requires_approval": False},
    )

    assert artifact["artifact_id"].startswith("art-")
    assert manager.list_all() == [artifact]
    assert manager.list_by_execution("exec-test") == [artifact]


def test_artifact_manager_blocks_invalid_status(tmp_path: Path) -> None:
    manager = ArtifactManager(tmp_path)

    try:
        manager.create(
            execution_id="exec-test",
            agent_id="growth-marketing-agent",
            workflow_id="manage-student-growth-journey",
            artifact_type="journey_state",
            source_action="persist_state",
            status="unknown",
        )
    except ValueError as exc:
        assert "status invalido" in str(exc)
    else:
        raise AssertionError("status invalido debio fallar")


def test_artifact_manager_blocks_missing_required_field(tmp_path: Path) -> None:
    manager = ArtifactManager(tmp_path)

    try:
        manager.create(
            execution_id="",
            agent_id="growth-marketing-agent",
            workflow_id="manage-student-growth-journey",
            artifact_type="journey_state",
            source_action="persist_state",
            status="draft",
        )
    except ValueError as exc:
        assert "campos requeridos vacios" in str(exc)
    else:
        raise AssertionError("campo requerido vacio debio fallar")


def test_artifact_manager_validates_record_against_core_schema(tmp_path: Path) -> None:
    manager = ArtifactManager(tmp_path)
    invalid_artifact = {
        "artifact_id": "art-test",
        "execution_id": "exec-test",
        "agent_id": "growth-marketing-agent",
        "workflow_id": "create-training-campaign",
        "artifact_type": "campaign",
        "source_action": "persist_artifacts",
        "status": "published",
        "metadata": {},
        "version": "0.1.0",
        "created_at": "2026-08-20T00:00:00+00:00",
    }

    try:
        manager._validate_artifact_record(invalid_artifact)
    except ValueError as exc:
        assert "artifact.schema.json" in str(exc)
    else:
        raise AssertionError("artifact fuera de schema debio fallar")
