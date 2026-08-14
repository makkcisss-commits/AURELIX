from aurelix_core.engine_factory import EngineFactory


def test_canonical_factory_wires_capability_escalation() -> None:
    factory = EngineFactory()
    assert factory.autonomy_fabric is not None
    assert factory.autonomy_fabric.capability_escalator is factory.capability_escalator
    run = factory.autonomy_fabric.run(
        "find a real opportunity",
        required_capabilities=["crm-write"],
    )
    assert run.status == "capability_learning_required"
    assert run.business["status"] == "blocked"
    assert run.academy["status"] == "learning_required"
    assert run.academy["capability_gaps"]
    assert len(factory.continuous_intelligence.objectives) == 1
    factory.autonomy_fabric.close()
