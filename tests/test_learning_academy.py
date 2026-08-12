from aurelix_core.academy import AcademyEngine
from aurelix_core.learning import LearningEngine, Outcome


def test_learning_is_traceable() -> None:
    engine = LearningEngine()
    item = engine.record(
        experiment_id="exp-1",
        outcome=Outcome.SUCCESS,
        observation="The offer produced qualified interest.",
        evidence_refs=["metric-1"],
        confidence=0.9,
    )
    assert item.evidence_refs == ("metric-1",)


def test_academy_requires_learning_reference() -> None:
    engine = AcademyEngine()
    try:
        engine.create_knowledge(
            title="Empty", summary="No evidence", learning_refs=[],
            source_refs=[], confidence=0.5,
        )
        assert False
    except ValueError:
        assert True
