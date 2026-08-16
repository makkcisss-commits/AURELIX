import pytest

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


def test_pipeline_enforces_max_steps() -> None:
    registry = EngineRegistry()
    for name in PIPELINE:
        registry.register(name, lambda payload, name=name: {name: "ok"})

    results = EngineeringPipeline(registry, PipelinePolicy(max_steps=3)).run({})

    assert [item.engine for item in results] == list(PIPELINE[:3])


def test_pipeline_rejects_invalid_limits() -> None:
    registry = EngineRegistry()
    registry.register("governor", lambda payload: {"ok": True})

    with pytest.raises(ValueError, match="invalid pipeline policy"):
        EngineeringPipeline(registry, PipelinePolicy(max_steps=0))
