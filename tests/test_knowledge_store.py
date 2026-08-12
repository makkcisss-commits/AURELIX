from aurelix_runtime.integrated_engines import KnowledgeItem
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository, KnowledgeQuery


def test_knowledge_repository_put_get_and_search():
    repo = InMemoryKnowledgeRepository()
    item = KnowledgeItem("k1", "Research lesson", "validated finding", tags=["research"])
    repo.put(item)
    assert repo.get("k1") == item
    assert repo.search(KnowledgeQuery("validated", ("research",), 10)) == [item]
