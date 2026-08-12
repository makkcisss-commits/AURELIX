from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class ExecutionLimits:
    """Hard runtime limits for one bounded task."""

    max_actions: int = 25
    max_tool_calls: int = 50
    max_runtime_seconds: int = 900
    max_cost_eur: float = 0.0


@dataclass(frozen=True)
class ExecutionUsage:
    actions: int = 0
    tool_calls: int = 0
    cost_eur: float = 0.0
    started_at: datetime | None = None


class LimitExceeded(Exception):
    pass


def check_limits(
    usage: ExecutionUsage,
    limits: ExecutionLimits,
    *,
    additional_actions: int = 0,
    additional_tool_calls: int = 0,
    additional_cost_eur: float = 0.0,
    now: datetime | None = None,
) -> None:
    if usage.actions + additional_actions > limits.max_actions:
        raise LimitExceeded("maximum actions exceeded")
    if usage.tool_calls + additional_tool_calls > limits.max_tool_calls:
        raise LimitExceeded("maximum tool calls exceeded")
    if usage.cost_eur + additional_cost_eur > limits.max_cost_eur:
        raise LimitExceeded("maximum task cost exceeded")
    if usage.started_at is not None:
        current = now or datetime.now(timezone.utc)
        elapsed = current - usage.started_at
        if elapsed > timedelta(seconds=limits.max_runtime_seconds):
            raise LimitExceeded("maximum runtime exceeded")
