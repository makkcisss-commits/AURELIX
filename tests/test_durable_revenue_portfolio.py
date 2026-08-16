from decimal import Decimal

from aurelix_core.durable_revenue_portfolio import DurableRevenuePortfolio
from aurelix_core.revenue_portfolio import PortfolioTarget, SourceStatus
from aurelix_runtime.persistence import RuntimeStore


def test_revenue_portfolio_survives_restart(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    portfolio = DurableRevenuePortfolio(
        store,
        PortfolioTarget(minimum_sources=1, preferred_sources=1, maximum_sources=10),
    )

    source = portfolio.discover(
        owner_role="owner",
        name="verified-channel",
        channel="service",
        expected_daily_eur=Decimal("20"),
        confidence=0.9,
        risk=0.1,
        connector="real-connector",
    )
    portfolio.approve(source.source_id)
    portfolio.activate(source.source_id)
    portfolio.record_realized_daily(source.source_id, Decimal("12.50"))
    store.close()

    restored_store = RuntimeStore(db)
    restored = DurableRevenuePortfolio(restored_store)
    restored_source = restored.get(source.source_id)

    assert restored_source.status == SourceStatus.ACTIVE
    assert restored_source.realized_daily_eur == Decimal("12.50")
    assert restored_source.expected_daily_eur == Decimal("20")
    assert restored_source.connector == "real-connector"
    assert restored.health()["daily_realized_eur"] == Decimal("12.50")
    assert len(restored.events()) >= 4
    restored_store.close()


def test_existing_revenue_portfolio_contract_is_preserved(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    portfolio = DurableRevenuePortfolio(store)
    source = portfolio.discover(
        owner_role="owner",
        name="candidate",
        channel="service",
        confidence=0.8,
        risk=0.2,
    )
    assert portfolio.get(source.source_id) is source
    assert portfolio.all() == [source]
    store.close()
