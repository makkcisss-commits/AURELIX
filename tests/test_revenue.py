from decimal import Decimal
import pytest

from aurelix_core.revenue import RevenueEngine


def test_synthetic_revenue_is_explicit_and_excluded_from_productive_totals() -> None:
    engine = RevenueEngine()
    engine.record(activity_id="activity-1", amount_eur=Decimal("120"), source="invoice", synthetic=True)
    engine.record(activity_id="activity-1", amount_eur=Decimal("80"), source="subscription", external_reference="external-80")
    assert engine.total_for_activity("activity-1") == Decimal("200")
    assert engine.total_for_activity("activity-1", productive_only=True) == Decimal("80")


def test_productive_revenue_requires_external_reference() -> None:
    with pytest.raises(ValueError, match="externally verifiable"):
        RevenueEngine().record(activity_id="activity-1", amount_eur=Decimal("1"), source="invoice")


def test_negative_revenue_is_rejected() -> None:
    with pytest.raises(ValueError):
        RevenueEngine().record(activity_id="activity-1", amount_eur=Decimal("-1"), source="test", synthetic=True)
