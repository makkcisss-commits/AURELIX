from decimal import Decimal

import pytest

from aurelix_core.economic_attribution import EconomicAttributionLedger
from aurelix_core.verified_economic_learning import VerifiedEconomicLearning


def _ledger() -> EconomicAttributionLedger:
    ledger = EconomicAttributionLedger()
    ledger.record(
        opportunity_id="opp-1",
        source_id="source-1",
        expected_daily_eur=Decimal("100"),
        observed_daily_eur=Decimal("125"),
        governor_decision_id="gov-1",
        resource_scope="scope-a",
        verified=True,
        external_reference="ext-1",
    )
    return ledger


def test_only_verified_attribution_becomes_learning_signal():
    learning = VerifiedEconomicLearning(_ledger())

    signals = learning.signals()

    assert len(signals) == 1
    assert signals[0].opportunity_id == "opp-1"
    assert signals[0].governor_decision_id == "gov-1"
    assert signals[0].variance_daily_eur == Decimal("25")
    assert signals[0].realization_ratio == Decimal("1.25")
    assert signals[0].evidence_type == "verified_economic_outcome"


def test_emit_is_idempotent():
    learning = VerifiedEconomicLearning(_ledger())

    assert len(learning.emit()) == 1
    assert learning.emit() == []


def test_learning_context_has_no_authority():
    context = VerifiedEconomicLearning(_ledger()).learning_context()

    assert context["authority"] == "none"
    assert context["execution_allowed"] is False


def test_attribution_rejects_unverified_input_before_learning():
    ledger = EconomicAttributionLedger()

    with pytest.raises(ValueError, match="only verified"):
        ledger.record(
            opportunity_id="opp-1",
            source_id="source-1",
            expected_daily_eur=Decimal("100"),
            observed_daily_eur=Decimal("125"),
            governor_decision_id="gov-1",
            resource_scope="scope-a",
            verified=False,
        )


def test_attribution_requires_governor_provenance():
    ledger = EconomicAttributionLedger()

    with pytest.raises(ValueError, match="governor_decision_id"):
        ledger.record(
            opportunity_id="opp-1",
            source_id="source-1",
            expected_daily_eur=Decimal("100"),
            observed_daily_eur=Decimal("125"),
            resource_scope="scope-a",
            verified=True,
        )
