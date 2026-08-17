from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from aurelix_core.academy import AcademyEngine
from aurelix_runtime.persistence import RuntimeStore


def test_knowledge_survives_restart(tmp_path) -> None:
    db_path = tmp_path / "academy.db"
    first = AcademyEngine(RuntimeStore(db_path))
    item = first.create_knowledge(
        title="Durable lesson",
        summary="A lesson that must survive restart",
        learning_refs=["learning-1"],
        source_refs=["source-1"],
        confidence=0.9,
    )

    second = AcademyEngine(RuntimeStore(db_path))
    restored = second.get(item.knowledge_id)
    assert restored == item


def test_concurrent_academy_writers_do_not_lose_knowledge(tmp_path) -> None:
    db_path = tmp_path / "academy-concurrent.db"

    def create(index: int) -> str:
        engine = AcademyEngine(RuntimeStore(db_path))
        item = engine.create_knowledge(
            title=f"Lesson {index}",
            summary=f"Concurrent lesson {index}",
            learning_refs=[f"learning-{index}"],
            source_refs=[f"source-{index}"],
            confidence=0.8,
        )
        return item.knowledge_id

    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(create, range(32)))

    restored = AcademyEngine(RuntimeStore(db_path))
    assert len(ids) == 32
    assert len(set(ids)) == 32
    assert {item.knowledge_id for item in restored.all()} == set(ids)


def test_direct_academy_run_binds_the_supplied_store_for_later_durable_knowledge(tmp_path) -> None:
    db_path = tmp_path / "academy-direct-run.db"
    store = RuntimeStore(db_path)
    academy = AcademyEngine()

    result = academy.run({"objective": "durable direct academy", "evidence": [], "status": "no_evidence"}, store)
    assert result["status"] == "insufficient_evidence"

    item = academy.create_knowledge(
        title="Direct durable lesson",
        summary="Created after Academy received its runtime store through run",
        learning_refs=["learning-direct"],
        source_refs=["source-direct"],
        confidence=0.8,
    )
    store.close()

    reopened = RuntimeStore(db_path)
    restored = AcademyEngine(reopened).get(item.knowledge_id)
    assert restored == item
    reopened.close()
