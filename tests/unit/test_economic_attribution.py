from concurrent.futures import ProcessPoolExecutor
from decimal import Decimal
from pathlib import Path

import pytest

from aurelix_core.economic_attribution import EconomicAttributionLedger
from aurelix_runtime.persistence import RuntimeStore


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


def _record_from_process(db_path: str) -> EconomicAttributionLedger:
    store = RuntimeStore(db_path)
    try:
        ledger = EconomicAttributionLedger(store)
        return ledger.record(
            opportunity_id="opp-concurrent",
            source_id="provider",
            governor_decision_id="gov-concurrent",
            expected_daily_eur=Decimal("10"),
            observed_daily_eur=Decimal("12"),
            verified=True,
            external_reference="payment-concurrent-1",
        )
    finally:
        store.close()


def test_same_external_reference_is_unique_across_processes(tmp_path: Path) -> None:
    db_path = str(tmp_path / "economic-attribution.db")
    with ProcessPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_record_from_process, [db_path] * 16))

    assert len(results) == 16
    assert all(result.external_reference == "payment-concurrent-1" for result in results)
    store = RuntimeStore(db_path)
    try:
        ledger = EconomicAttributionLedger(store)
        assert len(ledger.all()) == 1
        assert ledger.all()[0].observed_daily_eur == Decimal("12")
    finally:
        store.close()
