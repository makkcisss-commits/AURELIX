from decimal import Decimal
import pytest

from aurelix_core.innovation import InnovationStage, propose_innovation


def test_innovation_requires_knowledge_and_produces_score() -> None:
    item = propose_innovation(
        title="Automated market brief",
        knowledge_refs=["knowledge-1"],
        problem="Research synthesis is slow",
        proposed_solution="Build a bounded internal briefing workflow",
        expected_value="Faster opportunity discovery",
        estimated_cost_eur=Decimal("0"),
        risk=2,
        confidence=Decimal("0.8"),
    )
    assert item.stage is InnovationStage.PROPOSED
    assert item.priority_score > 0


def test_innovation_without_knowledge_is_rejected() -> None:
    with pytest.raises(ValueError):
        propose_innovation(
            title="Unsupported idea", knowledge_refs=[], problem="p",
            proposed_solution="s", expected_value="v",
            estimated_cost_eur=Decimal("0"), risk=1,
            confidence=Decimal("0.5"),
        )
