from aurelix_runtime.integrated_engines import KnowledgeItem
from aurelix_runtime.knowledge_context import KnowledgeContextBuilder
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository


def test_context_is_bounded_to_validated_knowledge():
    repo = InMemoryKnowledgeRepository()
    repo.put(KnowledgeItem("k1", "Validated topic", "known result", tags=["validated"]))
    repo.put(KnowledgeItem("k2", "Draft topic", "draft result", tags=["draft"]))
    context = KnowledgeContextBuilder(repo).build("topic")
    assert [item.id for item in context.items] == ["k1"]
    assert "known result" in context.as_text()
    assert "draft result" not in context.as_text()
