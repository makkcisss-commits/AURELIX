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
    assert state.active_execution_id in {"resume-a", "resume-b"}
    jobs = [store.get("resume-a"), store.get("resume-b")]
    assert sum(job is not None for job in jobs) == 1
    assert sum(job is not None and job.status == "queued" for job in jobs) == 1
    store.close()
