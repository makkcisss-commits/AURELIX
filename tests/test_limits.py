from datetime import datetime, timedelta, timezone

import pytest

from aurelix_core.limits import ExecutionLimits, ExecutionUsage, LimitExceeded, check_limits


def test_limits_allow_bounded_task() -> None:
    limits = ExecutionLimits(max_actions=3, max_tool_calls=4, max_cost_eur=2.0)
    usage = ExecutionUsage(actions=1, tool_calls=1, cost_eur=0.5)
    check_limits(usage, limits, additional_actions=2, additional_tool_calls=3, additional_cost_eur=1.5)


def test_action_limit_fails_closed() -> None:
    with pytest.raises(LimitExceeded):
        check_limits(ExecutionUsage(actions=3), ExecutionLimits(max_actions=3), additional_actions=1)


def test_cost_limit_fails_closed() -> None:
    with pytest.raises(LimitExceeded):
        check_limits(ExecutionUsage(cost_eur=0.9), ExecutionLimits(max_cost_eur=1.0), additional_cost_eur=0.2)


def test_runtime_limit_fails_closed() -> None:
    started = datetime.now(timezone.utc) - timedelta(seconds=11)
    usage = ExecutionUsage(started_at=started)
    limits = ExecutionLimits(max_runtime_seconds=10)
    with pytest.raises(LimitExceeded):
        check_limits(usage, limits)
