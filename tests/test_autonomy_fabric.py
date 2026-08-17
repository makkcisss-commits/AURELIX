from pathlib import Path
from uuid import uuid4

from aurelix_core.adaptive_loop import AdaptiveLoop
from aurelix_core.capability_escalation import CapabilityEscalator
from aurelix_core.continuous_intelligence import ContinuousIntelligence, EvidenceKind
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


def test_production_resume_path_preserves_mission_identity_and_creates_one_new_execution(tmp_path: Path) -> None:
    db = tmp_path / "resume.db"
    store = RuntimeStore(db)
    intelligence = ContinuousIntelligence()
    adaptive = AdaptiveLoop(intelligence, CapabilityEscalator(intelligence), durable_store=store)
    fabric = AutonomyFabric(store=store, adaptive_loop=adaptive)

    mission_id = "mission-production-resume"
    parent_execution_id = "execution-parent"
    capability = "crm-write"
    objective = "resume a governed CRM workflow"
    fabric.resume_coordinator.register(
        mission_id=mission_id,
        objective=objective,
        required_capabilities=[capability],
    )
    fabric.resume_coordinator.block(
        mission_id=mission_id,
        execution_id=parent_execution_id,
        reason="capability_learning_required",
    )
    adaptive.register_mission(parent_execution_id, objective, [capability])
    _, learning_objective = adaptive.block_for_capability(
        parent_execution_id,
        capability,
        reason="CRM write operation is not available",
        requested_by="business",
    )
    experiment = intelligence.propose_experiment(
        objective_id=learning_objective.objective_id,
        hypothesis="CRM write succeeds under the governed test contract",
        method="execute isolated CRM write benchmark",
        success_criteria=("write succeeds",),
    )
    evidence = adaptive.record_evidence(
        objective_id=learning_objective.objective_id,
        kind=EvidenceKind.EXPERIMENT,
        reference=experiment.experiment_id,
        strength=0.95,
    )
    evaluation = intelligence.evaluate(
        objective_id=learning_objective.objective_id,
        score=0.95,
        evidence_refs=(evidence.evidence_id,),
    )
    adaptive.validate_learning(
        execution_id=parent_execution_id,
        capability=capability,
        objective_id=learning_objective.objective_id,
        evaluation_id=evaluation.evaluation_id,
        evidence_refs=(evidence.evidence_id,),
    )

    resumed = fabric.resume_mission(mission_id)
    assert resumed.job_id != parent_execution_id
    state = fabric.resume_coordinator.get(mission_id)
    assert state is not None
    assert state.mission_id == mission_id
    assert state.parent_execution_id == parent_execution_id
    assert state.active_execution_id == resumed.job_id
    assert resumed.payload["mission_id"] == mission_id

    fabric.close()
    store.close()

    reopened = RuntimeStore(db)
    restarted_adaptive = AdaptiveLoop(ContinuousIntelligence(), CapabilityEscalator(ContinuousIntelligence()), durable_store=reopened)
    restarted_fabric = AutonomyFabric(store=reopened, adaptive_loop=restarted_adaptive)
    restarted_state = restarted_fabric.resume_coordinator.get(mission_id)
    assert restarted_state is not None
    assert restarted_state.parent_execution_id == parent_execution_id
    assert restarted_state.active_execution_id == resumed.job_id
    restarted_fabric.close()
    reopened.close()
