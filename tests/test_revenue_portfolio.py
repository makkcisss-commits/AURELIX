from decimal import Decimal

import pytest

from aurelix_core.revenue_portfolio import RevenuePortfolio, SourceStatus


def test_portfolio_tracks_target_without_fabricating_revenue():
    portfolio = RevenuePortfolio()
    source = portfolio.discover(
        owner_role="business",
        name="Example channel",
        channel="marketplace",
        expected_daily_eur=Decimal("1"),
        confidence=0.9,
        risk=0.1,
        connector="test-connector",
    )
    assert source.status == SourceStatus.DISCOVERED
    assert portfolio.health()["daily_realized_eur"] == Decimal("0")
    assert portfolio.health()["minimum_target_met"] is False


def test_activation_requires_real_connector_and_approval():
    portfolio = RevenuePortfolio()
    source = portfolio.discover(owner_role="business", name="x", channel="web", confidence=0.9, risk=0.1)
    with pytest.raises(PermissionError):
        portfolio.activate(source.source_id)
    portfolio.approve(source.source_id)
    with pytest.raises(RuntimeError):
        portfolio.activate(source.source_id)


def test_degraded_source_can_be_replaced_by_viable_source():
    portfolio = RevenuePortfolio()
    failed = portfolio.discover(owner_role="business", name="old", channel="web", confidence=0.9, risk=0.1, connector="old")
    portfolio.approve(failed.source_id)
    portfolio.activate(failed.source_id)
    portfolio.record_realized_daily(failed.source_id, Decimal("0"))

    candidate = portfolio.discover(owner_role="business", name="new", channel="marketplace", confidence=0.9, risk=0.1, connector="new")
    portfolio.approve(candidate.source_id)
    replacement = portfolio.replace(failed.source_id, candidate.source_id)

    assert failed.status == SourceStatus.RETIRED
    assert replacement.status == SourceStatus.ACTIVE
    assert replacement.replacement_for == failed.source_id
