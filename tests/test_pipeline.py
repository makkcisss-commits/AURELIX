from aurelix_runtime.engine_registry import EngineRegistry
from aurelix_runtime.pipeline import EngineeringPipeline, PipelinePolicy, PIPELINE


def test_pipeline_runs_in_order_and_stops_before_business_by_default() -> None:
    registry = EngineRegistry()
    seen: list[str] = []
    for name in PIPELINE:
        registry.register(name, lambda payload, name=name: (seen.append(name) or {name: "ok"}))

    results = EngineeringPipeline(registry).run({"goal": "first revenue"})

    assert [item.engine for item in results] == list(PIPELINE[:-1])
    assert seen == list(PIPELINE[:-1])


def test_business_requires_explicit_policy() -> None:
    registry = EngineRegistry()
    for name in PIPELINE:
        registry.register(name, lambda payload, name=name: {name: "ok"})

    results = EngineeringPipeline(registry, PipelinePolicy(allow_business=True)).run({})
    assert [item.engine for item in results] == list(PIPELINE)
