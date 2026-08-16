from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .engine_registry import EngineRegistry, EngineResult
from .execution_plane import ExecutionPlane, ExecutionScope


PIPELINE = (
    "governor",
    "research",
    "academy",
    "knowledge",
    "innovation",
    "experiment",
    "evaluation",
    "opportunity",
    "business",
)


@dataclass(frozen=True)
class PipelinePolicy:
    allow_business: bool = False
    max_steps: int = len(PIPELINE)
    max_runtime_seconds: float = 30.0

    def validate(self) -> None:
        if self.max_steps < 1 or self.max_runtime_seconds <= 0:
            raise ValueError("invalid pipeline policy")


class EngineeringPipeline:
    """Runs the central AURELIX loop through the fail-closed execution boundary."""

    def __init__(self, engines: EngineRegistry, policy: PipelinePolicy | None = None) -> None:
        self.engines = engines
        self.policy = policy or PipelinePolicy()
        self.policy.validate()
        self.execution = ExecutionPlane()
        for name in engines.names():
            self.execution.register(name, engines.handler(name))

    def run(self, initial: dict[str, Any]) -> list[EngineResult]:
        results: list[EngineResult] = []
        state = dict(initial)
        allowed = set(self.engines.names())
        if not self.policy.allow_business:
            allowed.discard("business")

        scope = ExecutionScope(
            agent_id="engineering-pipeline",
            allowed_engines=frozenset(allowed),
            max_steps=self.policy.max_steps,
            max_runtime_seconds=self.policy.max_runtime_seconds,
            environment="production",
        )

        for index, name in enumerate(PIPELINE):
            if index >= self.policy.max_steps:
                break
            if name == "business" and not self.policy.allow_business:
                break
            receipt = self.execution.execute(scope, name, state)
            result = EngineResult(
                engine=receipt.engine,
                status=receipt.status,
                output=receipt.output,
            )
            results.append(result)
            state = {**state, **result.output, "previous_engine": name}
        return results
