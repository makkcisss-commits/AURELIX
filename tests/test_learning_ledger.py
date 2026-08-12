from aurelix_runtime.learning_ledger import LearningLedger


def test_learning_ledger_links_research_evaluation_and_knowledge():
    learning = LearningLedger()
    research = learning.record_research("research-1", ["evidence-1"])
    evaluation = learning.record_evaluation("evaluation-1", "experiment-1", ["evidence-1"])
    knowledge = learning.record_knowledge("knowledge-1", ["evaluation-1"])
    assert research.parent_ids == ("evidence-1",)
    assert evaluation.parent_ids == ("experiment-1", "evidence-1")
    assert knowledge.parent_ids == ("evaluation-1",)
    assert len(learning.ledger.lineage("knowledge-1")) >= 3
