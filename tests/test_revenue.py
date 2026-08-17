from datetime import datetime, timezone
from decimal import Decimal
import pytest

from aurelix_core.revenue import RevenueEngine, RevenueRecord


def test_revenue_is_recorded_per_activity() -> None:
    engine = RevenueEngine()
    engine.record(activity_id="activity-1", amount_eur=Decimal("120"), source="invoice")
    engine.record(activity_id="activity-1", amount_eur=Decimal("80"), source="subscription")
    assert engine.total_for_activity("activity-1") == Decimal("200")
    assert engine.verified_total_for_activity("activity-1") == Decimal("0")


def test_negative_revenue_is_rejected() -> None:
    with pytest.raises(ValueError):
        RevenueEngine().record(activity_id="activity-1", amount_eur=Decimal("-1"), source="test")


def test_external_reference_marks_observation_verified_and_learning_eligible() -> None:
    engine = RevenueEngine()
    record = engine.record(
        activity_id="activity-external",
        amount_eur=Decimal("25.00"),
        source="payment-provider",
        external_reference=" payment-verified ",
    )
    assert record.verified_external is True
    assert record.external_reference == "payment-verified"
    assert engine.verified_total_for_activity("activity-external") == Decimal("25.00")
    assert engine.learning_evidence() == [record]


def test_verified_external_revenue_is_idempotent_and_learning_only_sees_verified() -> None:
    engine = RevenueEngine()
    first = engine.record_verified_external(
        activity_id="activity-2",
        amount_eur=Decimal("25.00"),
        source="payment-provider",
        external_reference="payment-123",
    )
    second = engine.record_verified_external(
        activity_id="activity-2",
        amount_eur=Decimal("25.00"),
        source="payment-provider",
        external_reference="payment-123",
    )
    assert second == first
    assert engine.verified_total_for_activity("activity-2") == Decimal("25.00")
    assert engine.learning_evidence() == [first]


def test_verified_external_reference_cannot_be_rebound() -> None:
    engine = RevenueEngine()
    engine.record_verified_external(
        activity_id="activity-3",
        amount_eur=Decimal("10"),
        source="payment-provider",
        external_reference="payment-456",
    )
    with pytest.raises(ValueError):
        engine.record_verified_external(
            activity_id="activity-4",
            amount_eur=Decimal("11"),
            source="payment-provider",
            external_reference="payment-456",
        )


def test_revenue_record_keeps_legacy_positional_constructor_compatibility() -> None:
    recorded_at = datetime.now(timezone.utc)
    record = RevenueRecord(
        "revenue-1",
        "activity-1",
        Decimal("10"),
        "invoice",
        None,
        recorded_at,
    )
    assert record.verified_external is False
    assert record.recorded_at == recorded_at
