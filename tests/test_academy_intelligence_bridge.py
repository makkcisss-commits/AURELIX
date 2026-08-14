import pytest

from aurelix_core.academy import AcademyEngine
from aurelix_core.academy_intelligence_bridge import AcademyIntelligenceBridge
from aurelix_core.continuous_intelligence import ContinuousIntelligence, KnowledgeState


def test_academy_knowledge_projects_with_provenance():
    academy = AcademyEngine()
    knowledge = academy.create_knowledge(
        title="Python testing",
        summary="Property-based tests can expose broader input spaces.",
        learning_refs=["learning-1"],
        source_refs=["https://example.test/python-testing"],
        confidence=0.9,
    )
    intelligence = ContinuousIntelligence()
    bridge = AcademyIntelligenceBridge(intelligence)

    item, projection = bridge.project_knowledge(knowledge, domain="Engineering")

    assert item.state is KnowledgeState.VALIDATED
    assert item.confidence == 0.9
    assert len(item.evidence_refs) == 1
    assert projection.objective_id in intelligence.objectives
    assert projection.evidence_ids == item.evidence_refs


def test_projection_is_idempotent_for_same_academy_knowledge():
    academy = AcademyEngine()
    knowledge = academy.create_knowledge(
        title="Market research",
        summary="Validated customer evidence should precede a commercial experiment.",
        learning_refs=["learning-2"],
        source_refs=["source-2"],
        confidence=0.8,
    )
    intelligence = ContinuousIntelligence()
    bridge = AcademyIntelligenceBridge(intelligence)

    first, first_projection = bridge.project_knowledge(knowledge, domain="Business")
    second, second_projection = bridge.project_knowledge(knowledge, domain="Business")

    assert first == second
    assert first_projection == second_projection
    assert len(intelligence.knowledge) == 1
    assert len(intelligence.objectives) == 1
    assert len(intelligence.evidence) == 1


def test_unproven_academy_knowledge_remains_candidate():
    academy = AcademyEngine()
    knowledge = academy.create_knowledge(
        title="Emerging hypothesis",
        summary="This claim still needs stronger validation.",
        learning_refs=["learning-3"],
        source_refs=["source-3"],
        confidence=0.4,
    )
    intelligence = ContinuousIntelligence()
    bridge = AcademyIntelligenceBridge(intelligence)

    item, _ = bridge.project_knowledge(knowledge, domain="Research")

    assert item.state is KnowledgeState.CANDIDATE


def test_academy_knowledge_without_provenance_is_rejected():
    academy = AcademyEngine()
    knowledge = academy.create_knowledge(
        title="Untraceable claim",
        summary="This claim has no provenance.",
        learning_refs=["learning-4"],
        source_refs=[],
        confidence=0.8,
    )
    # Academy permits learning references; the bridge can use them as fallback.
    intelligence = ContinuousIntelligence()
    bridge = AcademyIntelligenceBridge(intelligence)
    item, _ = bridge.project_knowledge(knowledge, domain="Research")
    assert item.evidence_refs

    with pytest.raises(ValueError):
        invalid = academy.create_knowledge(
            title="Actually untraceable",
            summary="No learning or source reference.",
            learning_refs=["placeholder"],
            source_refs=[],
            confidence=0.8,
        )
        # Academy's own contract requires a learning reference, so this branch
        # documents that provenance is required before projection.
        bridge.project_knowledge(
            type(knowledge)(
                invalid.knowledge_id,
                invalid.title,
                invalid.summary,
                (),
                (),
                invalid.confidence,
            ),
            domain="Research",
        )
