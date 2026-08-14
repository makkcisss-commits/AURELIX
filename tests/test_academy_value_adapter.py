from decimal import Decimal

import pytest

from aurelix_core.academy import AcademyEngine
from aurelix_core.academy_value_adapter import AcademyValueAdapter
from aurelix_core.value_discovery import ValueModel


def test_academy_knowledge_becomes_value_signal() -> None:
    academy = AcademyEngine()
    knowledge = academy.create_knowledge(
        title="Validated market insight",
        summary="A validated insight with traceable sources.",
        learning_refs=["learning-1"],
        source_refs=["source-1"],
        confidence=0.8,
    )

    signal = AcademyValueAdapter().to_signal(
        knowledge,
        capability_id="capability-market-analysis",
        value_model=ValueModel.SERVICES,
        expected_value_eur=Decimal("2500"),
        effort=4,
        risk=2,
    )

    assert signal.source_id == knowledge.knowledge_id
    assert signal.capability_id == "capability-market-analysis"
    assert signal.description == knowledge.summary
    assert signal.evidence_strength == 8


def test_adapter_rejects_untraceable_knowledge() -> None:
    academy = AcademyEngine()
    knowledge = academy.create_knowledge(
        title="Untraceable candidate",
        summary="This must not enter the value pipeline.",
        learning_refs=["learning-1"],
        source_refs=[],
        confidence=0.9,
    )

    with pytest.raises(ValueError, match="source reference"):
        AcademyValueAdapter().to_signal(
            knowledge,
            capability_id="capability-1",
            value_model=ValueModel.CONTENT,
            expected_value_eur=Decimal("100"),
            effort=2,
            risk=1,
        )


def test_adapter_requires_capability() -> None:
    academy = AcademyEngine()
    knowledge = academy.create_knowledge(
        title="Knowledge",
        summary="Traceable knowledge.",
        learning_refs=["learning-1"],
        source_refs=["source-1"],
        confidence=1.0,
    )

    with pytest.raises(ValueError, match="capability_id"):
        AcademyValueAdapter().to_signal(
            knowledge,
            capability_id=" ",
            value_model=ValueModel.DIGITAL_PRODUCT,
            expected_value_eur=Decimal("100"),
            effort=2,
            risk=1,
        )
