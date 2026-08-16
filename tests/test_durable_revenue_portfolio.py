from decimal import Decimal

from aurelix_core.durable_revenue_portfolio import DurableRevenuePortfolio
from aurelix_runtime.persistence import RuntimeStore


def test_revenue_portfolio_survives_restart(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    portfolio = DurableRevenuePortfolio(store)
    source = portfolio.discover(owner_role="owner", name="verified-channel", channel="service", expected_daily_eur=Decimal("20"), confidence=0.9, risk=0.1, connector="real-connector")
    portfolio.approve(source.source_id)
    portfolio.activate(source.source_id)
    portfolio.record_realized_daily(source.source_id, Decimal("12.50"), external_reference="external-payment-1")
    store.close()

    restored_store = RuntimeStore(db)
    restored = DurableRevenuePortfolio(restored_store)
    restored_source = restored.get(source.source_id)
    assert restored_source.realized_daily_eur == Decimal("12.50")
    assert restored_source.connector == "real-connector"
    assert restored.health()["daily_realized_eur"] == Decimal("12.50")
    assert any(event.get("external_reference") == "external-payment-1" for event in restored.events())
    restored_store.close()
