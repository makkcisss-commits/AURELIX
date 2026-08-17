from __future__ import annotations

import json
from pathlib import Path

from aurelix_runtime.autonomy_fabric import AutonomyFabric
from aurelix_runtime.persistence import RuntimeStore


def _mission_state(store: RuntimeStore, mission_id: str) -> dict:
    with store.lock:
        row = store.db.execute(
            "SELECT mission_id, status, parent_execution_id, active_execution_id, failed_execution_id "
            "FROM mission_state WHERE mission_id=?",
            (mission_id,),
        ).fetchone()
    assert row is not None
    return dict(row)


def test_resume_reservation_preserves_mission_identity_and_parent(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    mission_id = "mission-resume"
    parent_execution_id = "blocked-execution"

    fabric.resume_coordinator.register(
        mission_id=mission_id,
        objective="resume test",
        required_capabilities=[],
    )
    fabric.resume_coordinator.block(
        mission_id=mission_id,
        execution_id=parent_execution_id,
        reason="awaiting_provider",
    )

    execution_id = fabric.resume_coordinator.new_execution_id()
    assert fabric.resume_coordinator.reserve_resume(
        mission_id=mission_id,
        execution_id=execution_id,
    )

    state = _mission_state(store, mission_id)
    assert state["status"] == "resume_reserved"
    assert state["active_execution_id"] == execution_id
    assert state["parent_execution_id"] == parent_execution_id

    job = store.get(execution_id)
    assert job is not None
    payload = json.loads(json.dumps(job.payload))
    assert payload["mission_id"] == mission_id
    assert payload["objective"] == "resume test"

    fabric.close()


def test_concurrent_resume_reservation_converges_on_one_execution(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    mission_id = "mission-concurrent"
    parent_execution_id = "blocked-concurrent"

    fabric.resume_coordinator.register(
        mission_id=mission_id,
        objective="concurrent resume test",
        required_capabilities=[],
    )
    fabric.resume_coordinator.block(
        mission_id=mission_id,
        execution_id=parent_execution_id,
        reason="awaiting_provider",
    )

    first_id = fabric.resume_coordinator.new_execution_id()
    second_id = fabric.resume_coordinator.new_execution_id()

    first = fabric.resume_coordinator.reserve_resume(
        mission_id=mission_id,
        execution_id=first_id,
    )
    second = fabric.resume_coordinator.reserve_resume(
        mission_id=mission_id,
        execution_id=second_id,
    )

    assert first is True
    assert second is False
    state = _mission_state(store, mission_id)
    assert state["active_execution_id"] == first_id
    assert state["parent_execution_id"] == parent_execution_id
    assert store.get(second_id) is None

    fabric.close()
