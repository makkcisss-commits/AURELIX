from aurelix_runtime.integrated_engines import Evidence
from aurelix_runtime.knowledge_learning import KnowledgeLearningService
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository, KnowledgeQuery


def test_learning_persists_verified_evidence_only():
    repo = InMemoryKnowledgeRepository()
    service = KnowledgeLearningService(repo)
    result = service.learn(
        "objective",
        [
            Evidence("source-a", "validated lesson", 0.95, True),
            Evidence("source-b", "unverified claim", 0.2, False),
        ],
    )
    item = repo.get(result.knowledge_id)
    assert item is not None
    assert item.content == "validated lesson"
    assert len(item.evidence) == 1
    assert item.evidence[0].verified is True
    assert repo.search(KnowledgeQuery("validated lesson")) == [item]
