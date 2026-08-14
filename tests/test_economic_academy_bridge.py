from decimal import Decimal

from aurelix_core.academy import AcademyEngine
from aurelix_core.economic_academy_bridge import EconomicAcademyBridge
from aurelix_core.economic_feedback import EconomicFeedback
from aurelix_core.economic_learning_adapter import EconomicLearningAdapter


class Source:
    def __init__(self, source_id: str, observed: str, expected: str, productive: bool = True):
        self.source_id = source_id
        self.realized_daily_eur = Decimal(observed)
        self.expected_daily_eur = Decimal(expected)
        self.is_productive = productive


class Portfolio:
    def __init__(self, *sources):
        self.sources = list(sources)


def test_verified_economic_outcomes_publish_as_traceable_academy_knowledge():
    portfolio = Portfolio(Source("op-1", "25", "40"))
    learning = EconomicLearningAdapter(EconomicFeedback(portfolio))
    academy = AcademyEngine()

    knowledge = EconomicAcademyBridge(academy, learning).publish()

    assert len(knowledge) == 1
    item = knowledge[0]
    assert item.source_refs == ("op-1",)
    assert item.learning_refs == ("economic:op-1",)
    assert "Observed daily revenue EUR 25" in item.summary
    assert item.confidence == 1.0
    assert academy.get(item.knowledge_id) is item


def test_no_economic_evidence_creates_no_academy_knowledge():
    academy = AcademyEngine()
    learning = EconomicLearningAdapter(EconomicFeedback(Portfolio()))

    assert EconomicAcademyBridge(academy, learning).publish() == []
