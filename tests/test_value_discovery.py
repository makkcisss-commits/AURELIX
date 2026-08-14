from decimal import Decimal

import pytest

from aurelix_core.governor import Governor, GovernorRoute
from aurelix_core.value_discovery import ValueDiscovery, ValueModel, ValueSignal


def signal(**overrides):
    data = {
        "source_id": "academy-study-1",
        "capability_id": "cap-ai-video",
        "description": "Create a reusable AI video workflow",
        "value_model": ValueModel.CONTENT,
        "expected_value_eur": Decimal("2500"),
        "effort": 4,
        "risk": 2,
        "evidence_strength": 8,
    }
    data.update(overrides)
    return ValueSignal(**data)


def test_value_discovery_produces_ranked_non_executable_evaluation():
    discovery = ValueDiscovery()
    result = discovery.evaluate(signal())

    assert result.expected_value_eur == Decimal("2500")
    assert result.score > 0
    assert result.requires_governor is True
    assert result.governor_route is GovernorRoute.OWNER_REQUIRED


def test_value_discovery_is_idempotent():
    discovery = ValueDiscovery()
    first = discovery.evaluate(signal())
    second = discovery.evaluate(signal())

    assert second == first


def test_high_risk_opportunity_is_blocked_by_governor():
    discovery = ValueDiscovery(governor=Governor())
    result = discovery.evaluate(signal(risk=9))

    assert result.governor_route is GovernorRoute.BLOCKED
    assert "risk threshold exceeded" in result.reasons


def test_rank_orders_higher_value_and_evidence():
    discovery = ValueDiscovery()
    low = signal(source_id="low", expected_value_eur=Decimal("100"), evidence_strength=4, effort=8)
    high = signal(source_id="high", expected_value_eur=Decimal("50000"), evidence_strength=10, effort=2)

    ranked = discovery.rank([low, high])

    assert [item.source_id for item in ranked] == ["high", "low"]


def test_invalid_value_signal_is_rejected():
    with pytest.raises(ValueError):
        ValueDiscovery().evaluate(signal(expected_value_eur=Decimal("-1")))


def test_discovery_never_authorizes_execution():
    result = ValueDiscovery().evaluate(signal(expected_value_eur=Decimal("100")))

    assert result.requires_governor is True
    assert result.governor_route is GovernorRoute.POLICY_ALLOWED
