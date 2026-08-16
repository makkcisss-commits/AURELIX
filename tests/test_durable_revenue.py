from decimal import Decimal

from aurelix_core.durable_revenue import DurableRevenueLedger
from aurelix_runtime.persistence import RuntimeStore


def test_revenue_observation_survives_restart_and_duplicate_is_idempotent(tmp_path):
    path = tmp_path / "aurelix.db"

    store = RuntimeStore(path)
    ledger = DurableRevenueLedger(store)
    first = ledger.record(
        activity_id="source-1",
        amount_eur=Decimal("25.50"),
        source="channel-a",
        external_reference="external-123",
    )
    assert ledger.total_for_activity("source-1") == Decimal("25.50")
    store.db.close()

    store2 = RuntimeStore(path)
    ledger2 = DurableRevenueLedger(store2)
    replay = ledger2.record(
        activity_id="source-1",
        amount_eur=Decimal("25.50"),
        source="channel-a",
        external_reference="external-123",
    )

    assert replay.revenue_id == first.revenue_id
    assert ledger2.total_for_activity("source-1") == Decimal("25.50")
    store2.db.close()


def test_distinct_external_references_remain_distinct(tmp_path):
    store = RuntimeStore(tmp_path / "aurelix.db")
    ledger = DurableRevenueLedger(store)
    ledger.record(
        activity_id="source-1",
        amount_eur=Decimal("10"),
        source="channel-a",
        external_reference="external-1",
    )
    ledger.record(
        activity_id="source-1",
        amount_eur=Decimal("15"),
        source="channel-a",
        external_reference="external-2",
    )
    assert ledger.total_for_activity("source-1") == Decimal("25")
    store.db.close()
