import json
import time
from pathlib import Path

import pytest

from aurelix_runtime.autonomy_fabric import AutonomyFabric
from aurelix_runtime.experiment_runner import ExperimentRunner
from aurelix_runtime.integrated_engines import EngineStore, Evidence, ResearchEngine
from aurelix_runtime.knowledge_store import KnowledgeQuery, SQLiteKnowledgeRepository
from aurelix_runtime.persistence import RuntimeStore


def test_autonomy_fabric_runs_one_complete_chain_and_survives_restart(tmp_path: Path) -> None:
    db = tmp_path / "aurelix.db"

    def provider(_: str):
        return [Evidence(source="trusted", claim="validated fact", confidence=0.9, verified=True)]

    def measure(_experiment):
        # This test supplies the experiment's explicit measurement boundary.
        # The production runtime never invents this observation when no executor exists.
        return [{"success": 0.0}]

    store = RuntimeStore(db)
    runner = ExperimentRunner(collector=measure)
    fabric = AutonomyFabric(store=store, research=ResearchEngine(provider=provider), experiment_runner=runner)
    run = fabric.run("find a validated opportunity")
    durable = store.get_result(run.execution_id)

    assert run.status == "awaiting_validation"
    assert run.research["evidence"][0]["verified"] is True
    assert run.knowledge["validated"] is True
    assert run.experiment["experiment_id"]
    assert run.experiment["status"] == "complete"
    assert run.evaluation["passed"] is False
    assert run.evaluation["reason"] == "experiment_failed"
    assert run.opportunity["opportunity_id"] is None
    assert run.business["status"] == "awaiting_validation"
    assert store.get(run.execution_id).status == "completed"
    assert durable["status"] == "awaiting_validation"

    durable_knowledge = SQLiteKnowledgeRepository(store)
    items = durable_knowledge.search(KnowledgeQuery("validated fact", tags=("validated",)))
    assert len(items) == 1
    assert items[0].content == "validated fact"
    fabric.close()

    reopened = RuntimeStore(db)
    engines = EngineStore(runtime_store=reopened)
    assert engines.knowledge
    assert engines.experiments
    assert engines.opportunities == {}
    assert any(event["event"] == "knowledge.stored" for event in engines.audit)
    assert reopened.get_result(run.execution_id)["status"] == "awaiting_validation"
    reopened.close()


def test_knowledge_repository_is_restart_safe_and_queryable(tmp_path: Path) -> None:
    db = tmp_path / "knowledge.db"
    store = RuntimeStore(db)
    repo = SQLiteKnowledgeRepository(store)
    item = __import__("aurelix_runtime.integrated_engines", fromlist=["KnowledgeItem"]).KnowledgeItem(
        "k1", "Market fact", "A durable fact", [Evidence("source", "A durable fact", 1.0, True)], ["market", "validated"]
    )
    repo.put(item)
    assert repo.count() == 1
    store.close()

    reopened = RuntimeStore(db)
    repo2 = SQLiteKnowledgeRepository(reopened)
    found = repo2.search(KnowledgeQuery("durable", tags=("validated",)))
    assert found and found[0].id == "k1"
    reopened.close()


def test_autonomy_fabric_without_provider_never_fabricates_knowledge_or_business(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "aurelix.db")
    fabric = AutonomyFabric(store=store, research=ResearchEngine())

    run = fabric.run("research a new market")

    assert run.status == "awaiting_validation"
    assert run.research["status"] == "awaiting_provider"
    assert run.knowledge["knowledge_id"] is None
    assert run.opportunity["opportunity_id"] is None
    assert run.business["status"] == "awaiting_validation"
    assert store.status()["failed"] == 0
    fabric.close()


def _put_resume_state(store: RuntimeStore, blocked_execution_id: str, value: dict) -> None:
    with store.lock, store.db:
        store.db.execute(
            "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (f"mission-resume:{blocked_execution_id}", json.dumps(value, sort_keys=True)),
        )


def _get_resume_state(store: RuntimeStore, blocked_execution_id: str) -> dict:
    with store.lock:
        row = store.db.execute(
            "SELECT value FROM runtime_state WHERE key=?",
            (f"mission-resume:{blocked_execution_id}",),
        ).fetchone()
    return json.loads(row[0])


def test_expired_reserved_resume_can_be_reclaimed(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    blocked = "blocked-1"
    _put_resume_state(store, blocked, {"state": "reserved", "execution_id": "old-resume", "lease_until": time.time() - 1})

    resumed = fabric._claim_resume_execution(blocked)

    assert resumed != "old-resume"
    state = _get_resume_state(store, blocked)
    assert state["state"] == "reserved"
    assert state["execution_id"] == resumed
    assert state["lease_until"] > time.time()
    fabric.close()


def test_active_reserved_resume_is_still_single_owner(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    blocked = "blocked-2"
    _put_resume_state(store, blocked, {"state": "reserved", "execution_id": "active-resume", "lease_until": time.time() + 60})

    with pytest.raises(RuntimeError, match="already in progress"):
        fabric._claim_resume_execution(blocked)

    assert _get_resume_state(store, blocked)["execution_id"] == "active-resume"
    fabric.close()


def test_running_resume_is_reclaimable_when_runtime_execution_is_missing(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    blocked = "blocked-3"
    _put_resume_state(store, blocked, {"state": "running", "execution_id": "crashed-resume"})

    resumed = fabric._claim_resume_execution(blocked)

    assert resumed != "crashed-resume"
    assert _get_resume_state(store, blocked)["execution_id"] == resumed
    fabric.close()
