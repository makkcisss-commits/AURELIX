from aurelix_core.academy_governor_boundary import AcademyGovernorBoundary


def test_academy_proposal_requires_governor() -> None:
    engine = AcademyGovernorBoundary()
    proposal = engine.propose(
        knowledge_id="knowledge-1",
        title="Increase qualified outreach",
        rationale="Verified learning supports a larger outreach experiment.",
        learning_refs=["learning-1"],
    )
    assert proposal.requires_governor is True
    assert proposal.learning_refs == ("learning-1",)


def test_academy_proposal_rejects_missing_learning() -> None:
    engine = AcademyGovernorBoundary()
    try:
        engine.propose(
            knowledge_id="knowledge-1",
            title="Proposal",
            rationale="Reason",
            learning_refs=[],
        )
        assert False
    except ValueError:
        assert True
