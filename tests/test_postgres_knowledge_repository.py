import os

import pytest

from aurelix_runtime.integrated_engines import Evidence, KnowledgeItem
from aurelix_runtime.knowledge_store import KnowledgeQuery
from aurelix_runtime.postgres_knowledge_repository import PostgresKnowledgeRepository


@pytest.mark.skipif(
    not os.getenv("AURELIX_DATABASE_URL"),
    reason="PostgreSQL integration requires AURELIX_DATABASE_URL",
)
def test_postgres_knowledge_round_trip() -> None:
    repository = PostgresKnowledgeRepository(os.environ["AURELIX_DATABASE_URL"])
    item = KnowledgeItem(
        id="ci-postgres-round-trip",
        title="PostgreSQL integration proof",
        content="Source-backed knowledge survives a database round trip.",
        evidence=[Evidence("https://example.test/source", "database-backed claim", 0.9, True)],
        tags=["ci", "postgres"],
    )

    repository.put(item)

    loaded = repository.get(item.id)
    assert loaded is not None
    assert loaded.content == item.content
    assert loaded.evidence[0].source == item.evidence[0].source
    assert repository.count() >= 1
    assert repository.search(KnowledgeQuery("database-backed claim", limit=10))
