from pathlib import Path
from aurelix_core.capability_escalation import CapabilityEscalator
from aurelix_core.continuous_intelligence import ContinuousIntelligence
from aurelix_runtime.autonomy_fabric import AutonomyFabric
from aurelix_runtime.persistence import RuntimeStore

def test_unknown_runtime_capability_is_blocked_and_escalated(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "aurelix.db")
    intelligence = ContinuousIntelligence()
    fabric = AutonomyFabric(store=store, capability_escalator=CapabilityEscalator(intelligence))
    run = fabric.run("find a real opportunity", required_capabilities=["crm-write"])
    assert run.status == "capability_learning_required"
    assert run.business["status"] == "blocked"
    assert run.academy["status"] == "learning_required"
    assert run.academy["capability_gaps"]
    assert len(intelligence.objectives) == 1
    assert store.get(run.execution_id).status == "completed"
    assert any(event["event"] == "autonomy.capability_escalated" for event in store.audit)
    fabric.close()
