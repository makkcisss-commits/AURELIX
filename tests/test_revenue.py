from decimal import Decimal
import pytest

from aurelix_core.revenue import RevenueEngine


def test_revenue_is_recorded_per_activity() -> None:
    engine = RevenueEngine()
    engine.record(activity_id="activity-1", amount_eur=Decimal("120"), source="invoice")
    engine.record(activity_id="activity-1", amount_eur=Decimal("80"), source="subscription")
    assert engine.total_for_activity("activity-1") == Decimal("200")


def test_negative_revenue_is_rejected() -> None:
    with pytest.raises(ValueError):
        RevenueEngine().record(activity_id="activity-1", amount_eur=Decimal("-1"), source="test")
