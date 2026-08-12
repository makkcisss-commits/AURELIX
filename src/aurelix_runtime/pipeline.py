from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .engine_registry import EngineRegistry, EngineResult


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


class EngineeringPipeline:
    """Runs the central AURELIX loop using explicit registered capabilities."""

    def __init__(self, engines: EngineRegistry, policy: PipelinePolicy | None = None) -> None:
        self.engines = engines
        self.policy = policy or PipelinePolicy()

    def run(self, initial: dict[str, Any]) -> list[EngineResult]:
        results: list[EngineResult] = []
        state = dict(initial)
        for index, name in enumerate(PIPELINE):
            if index >= self.policy.max_steps:
                break
            if name == "business" and not self.policy.allow_business:
                break
            result = self.engines.execute(name, state)
            results.append(result)
            state = {**state, **result.output, "previous_engine": name}
        return results
