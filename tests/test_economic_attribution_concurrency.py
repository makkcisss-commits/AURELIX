from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

from aurelix_core.economic_attribution import EconomicAttributionLedger


def test_same_external_reference_is_idempotent_under_concurrent_recording() -> None:
    ledger = EconomicAttributionLedger()

    def record():
        return ledger.record(
            opportunity_id="op-1",
            source_id="source-1",
            expected_daily_eur=Decimal("10"),
            observed_daily_eur=Decimal("12"),
            governor_decision_id="decision-1",
            verified=True,
            external_reference="external-1",
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        entries = list(pool.map(lambda _: record(), range(32)))

    assert all(entry == entries[0] for entry in entries)
    assert ledger.all() == [entries[0]]
