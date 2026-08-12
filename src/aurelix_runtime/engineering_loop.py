from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class Stage(str, Enum):
    GOVERNOR = "GOVERNOR"
    RESEARCH = "RESEARCH"
    ACADEMY = "ACADEMY"
    KNOWLEDGE = "KNOWLEDGE"
    INNOVATION = "INNOVATION"
    EXPERIMENT = "EXPERIMENT"
    EVALUATION = "EVALUATION"
    OPPORTUNITY = "OPPORTUNITY"
    BUSINESS = "BUSINESS"


@dataclass
class LoopContext:
    objective: str
    data: dict[str, object] = field(default_factory=dict)
    history: list[Stage] = field(default_factory=list)


Handler = Callable[[LoopContext], LoopContext]


class EngineeringLoop:
    """Deterministic stage orchestrator; business/financial actions remain gated."""

    ORDER = (
        Stage.GOVERNOR,
        Stage.RESEARCH,
        Stage.ACADEMY,
        Stage.KNOWLEDGE,
        Stage.INNOVATION,
        Stage.EXPERIMENT,
        Stage.EVALUATION,
        Stage.OPPORTUNITY,
        Stage.BUSINESS,
    )

    def __init__(self) -> None:
        self._handlers: dict[Stage, Handler] = {}

    def register(self, stage: Stage, handler: Handler) -> None:
        self._handlers[stage] = handler

    def run(self, context: LoopContext, *, stop_before_business: bool = True) -> LoopContext:
        for stage in self.ORDER:
            if stop_before_business and stage == Stage.BUSINESS:
                break
            handler = self._handlers.get(stage)
            if handler is None:
                raise RuntimeError(f"missing handler for {stage.value}")
            context = handler(context)
            context.history.append(stage)
        return context

    def missing_stages(self) -> tuple[Stage, ...]:
        return tuple(stage for stage in self.ORDER if stage not in self._handlers)
