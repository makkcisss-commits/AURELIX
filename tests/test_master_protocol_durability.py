from decimal import Decimal

from aurelix_core.academy import AcademyEngine
from aurelix_core.economic_attribution import EconomicAttributionLedger
from aurelix_runtime.persistence import RuntimeStore


def test_canonical_academy_knowledge_survives_restart(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    academy = AcademyEngine(store=store)
    item = academy.create_knowledge(
        title="validated learning",
        summary="A durable fact",
        learning_refs=["learning-1"],
        source_refs=["https://example.invalid/evidence/1"],
        confidence=0.9,
    )
    store.close()

    restarted = RuntimeStore(db)
    restored = AcademyEngine(store=restarted).get(item.knowledge_id)
    assert restored == item
    restarted.close()


def test_verified_economic_attribution_is_durable_and_idempotent(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    ledger = EconomicAttributionLedger(store=store)
    entry = ledger.record(
        opportunity_id="op-1",
        source_id="source-1",
        expected_daily_eur=Decimal("12.50"),
        observed_daily_eur=Decimal("14.00"),
        governor_decision_id="decision-1",
        verified=True,
        external_reference="payment-event-1",
    )
    assert ledger.record(
        opportunity_id="op-1",
        source_id="source-1",
        expected_daily_eur=Decimal("12.50"),
        observed_daily_eur=Decimal("14.00"),
        governor_decision_id="decision-1",
        verified=True,
        external_reference="payment-event-1",
    ) == entry
    store.close()

    restarted = RuntimeStore(db)
    restored = EconomicAttributionLedger(store=restarted).all()
    assert restored == [entry]
    restarted.close()
