from concurrent.futures import ThreadPoolExecutor

from aurelix_runtime.mission_resume import MissionResumeCoordinator
from aurelix_runtime.persistence import RuntimeStore


def test_mission_identity_survives_restart(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    coordinator = MissionResumeCoordinator(store)
    coordinator.register(
        mission_id="mission-1",
        objective="validate a product opportunity",
        required_capabilities=["research-x"],
    )
    coordinator.block(
        mission_id="mission-1",
        execution_id="execution-1",
        reason="capability_learning_required",
    )
    store.close()

    restarted = RuntimeStore(db)
    state = MissionResumeCoordinator(restarted).get("mission-1")
    assert state is not None
    assert state.mission_id == "mission-1"
    assert state.objective == "validate a product opportunity"
    assert state.active_execution_id == "execution-1"
    assert state.parent_execution_id is None
    assert state.status == "blocked"
    restarted.close()


def test_concurrent_resume_requests_create_one_execution(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    coordinator = MissionResumeCoordinator(store)
    coordinator.register(
        mission_id="mission-2",
        objective="resume after validated learning",
        required_capabilities=["research-x"],
    )
    coordinator.block(
        mission_id="mission-2",
        execution_id="execution-parent",
        reason="capability_learning_required",
    )

    def reserve(execution_id):
        return coordinator.reserve_resume(mission_id="mission-2", execution_id=execution_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, ["resume-a", "resume-b"]))

    assert sorted(results) == [False, True]
    state = coordinator.get("mission-2")
    assert state is not None
    assert state.status == "resume_reserved"
    assert state.parent_execution_id == "execution-parent"
    assert state.active_execution_id in {"resume-a", "resume-b"}
    jobs = [store.get("resume-a"), store.get("resume-b")]
    assert sum(job is not None for job in jobs) == 1
    assert sum(job is not None and job.status == "queued" for job in jobs) == 1
    store.close()


def test_resume_parent_is_durable_after_restart(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    coordinator = MissionResumeCoordinator(store)
    coordinator.register(
        mission_id="mission-3",
        objective="resume with durable provenance",
        required_capabilities=["research-x"],
    )
    coordinator.block(
        mission_id="mission-3",
        execution_id="execution-parent",
        reason="capability_learning_required",
    )
    assert coordinator.reserve_resume(mission_id="mission-3", execution_id="resume-1")
    state = coordinator.get("mission-3")
    assert state is not None
    assert state.parent_execution_id == "execution-parent"
    assert state.active_execution_id == "resume-1"
    store.close()

    restarted = RuntimeStore(db)
    state = MissionResumeCoordinator(restarted).get("mission-3")
    assert state is not None
    assert state.parent_execution_id == "execution-parent"
    assert state.active_execution_id == "resume-1"
    assert state.status == "resume_reserved"
    restarted.close()


def test_first_successful_execution_can_establish_mission_authority(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    coordinator = MissionResumeCoordinator(store)
    coordinator.register(
        mission_id="mission-first",
        objective="complete first execution",
        required_capabilities=[],
    )

    state = coordinator.activate(mission_id="mission-first", execution_id="execution-first")

    assert state.status == "active"
    assert state.active_execution_id == "execution-first"
    assert state.parent_execution_id is None
    assert state.failed_execution_id is None
    store.close()


def test_resume_activation_still_requires_reserved_execution(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    coordinator = MissionResumeCoordinator(store)
    coordinator.register(
        mission_id="mission-fenced",
        objective="preserve resume fencing",
        required_capabilities=[],
    )
    coordinator.block(
        mission_id="mission-fenced",
        execution_id="execution-parent",
        reason="awaiting_validation",
    )
    assert coordinator.reserve_resume(mission_id="mission-fenced", execution_id="execution-resume")

    try:
        coordinator.activate(mission_id="mission-fenced", execution_id="wrong-execution")
    except RuntimeError as exc:
        assert "mission activation fenced" in str(exc)
    else:
        raise AssertionError("activation must reject an execution that does not own the reservation")

    store.close()


def test_unexpected_execution_reason_records_failed_provenance(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    coordinator = MissionResumeCoordinator(store)
    coordinator.register(
        mission_id="mission-failed",
        objective="preserve failed execution provenance",
        required_capabilities=[],
    )

    state = coordinator.block(
        mission_id="mission-failed",
        execution_id="execution-failed",
        reason="RuntimeError",
    )

    assert state.status == "blocked"
    assert state.active_execution_id is None
    assert state.failed_execution_id == "execution-failed"
    assert state.resume_state == "RuntimeError"
    store.close()
