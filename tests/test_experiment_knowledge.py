from aurelix_runtime.integrated_engines import Evidence
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository, KnowledgeQuery
from aurelix_runtime.experiment_knowledge import ExperimentKnowledgeService


def test_passed_evaluation_with_verified_evidence_becomes_knowledge():
    repo = InMemoryKnowledgeRepository()
    service = ExperimentKnowledgeService(repo)
    provenance = service.record_evaluation(
        "exp-1", "eval-1", "objective", "measured improvement", True,
        [Evidence("lab", "measurement", 0.99, True)],
    )
    assert provenance.passed is True
    items = repo.search(KnowledgeQuery("measured improvement", ("validated",), 10))
    assert len(items) == 1
    assert items[0].evidence[0].source == "lab"


def test_failed_evaluation_is_not_promoted():
    repo = InMemoryKnowledgeRepository()
    service = ExperimentKnowledgeService(repo)
    service.record_evaluation(
        "exp-2", "eval-2", "objective", "failed result", False,
        [Evidence("lab", "measurement", 0.99, True)],
    )
    assert repo.search(KnowledgeQuery("failed result")) == []
