from pathlib import Path

from aurelix_runtime.autonomy_fabric import AutonomyFabric
from aurelix_runtime.integrated_engines import EngineStore, Evidence, ResearchEngine
from aurelix_runtime.persistence import RuntimeStore


def test_autonomy_fabric_runs_one_complete_chain_and_survives_restart(tmp_path: Path) -> None:
    db = tmp_path / "aurelix.db"

    def provider(_: str):
        return [Evidence(source="trusted", claim="validated fact", confidence=0.9, verified=True)]

    store = RuntimeStore(db)
    fabric = AutonomyFabric(store=store, research=ResearchEngine(provider=provider))
    run = fabric.run("find a validated opportunity")

    assert run.status == "awaiting_approval"
    assert run.research["evidence"][0]["verified"] is True
    assert store.get(run.execution_id).status == "completed"
    assert store.get_result(run.execution_id)["opportunity"]["opportunity_id"]
    fabric.close()

    reopened = RuntimeStore(db)
    engines = EngineStore(runtime_store=reopened)
    assert engines.knowledge
    assert engines.experiments
    assert engines.opportunities
    assert any(event["event"] == "knowledge.stored" for event in engines.audit)
    assert reopened.get_result(run.execution_id)["status"] == "awaiting_approval"
    reopened.close()
