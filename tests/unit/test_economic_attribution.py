from decimal import Decimal

import pytest

from aurelix_core.economic_attribution import EconomicAttributionLedger


def test_records_verified_attribution_with_provenance():
    ledger = EconomicAttributionLedger()
    entry = ledger.record(
        opportunity_id="opp-1",
        source_id="src-1",
        governor_decision_id="gov-7",
        resource_scope="scope:marketing",
        expected_daily_eur=Decimal("10"),
        observed_daily_eur=Decimal("13.50"),
        verified=True,
        external_reference="payment-42",
    )
    assert entry.variance_daily_eur == Decimal("3.50")
    assert entry.net_daily_eur == Decimal("13.50")
    assert ledger.by_opportunity("opp-1") == [entry]
    assert ledger.learning_evidence()[0]["verified"] is True


def test_rejects_unverified_outcome():
    ledger = EconomicAttributionLedger()
    with pytest.raises(ValueError, match="verified"):
        ledger.record(
            opportunity_id="opp-1",
            source_id="src-1",
            governor_decision_id="gov-7",
            expected_daily_eur=Decimal("10"),
            observed_daily_eur=Decimal("13.50"),
            verified=False,
        )


def test_requires_governor_provenance():
    ledger = EconomicAttributionLedger()
    with pytest.raises(ValueError, match="governor_decision_id"):
        ledger.record(
            opportunity_id="opp-1",
            source_id="src-1",
            expected_daily_eur=Decimal("10"),
            observed_daily_eur=Decimal("13.50"),
            verified=True,
        )


def test_same_external_observation_is_idempotent():
    ledger = EconomicAttributionLedger()
    kwargs = dict(
        opportunity_id="opp-1",
        source_id="src-1",
        governor_decision_id="gov-7",
        expected_daily_eur=Decimal("10"),
        observed_daily_eur=Decimal("13.50"),
        verified=True,
        external_reference="payment-42",
    )
    first = ledger.record(**kwargs)
    second = ledger.record(**kwargs)
    assert first == second
    assert len(ledger.all()) == 1
