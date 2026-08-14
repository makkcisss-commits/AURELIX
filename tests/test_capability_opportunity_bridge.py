import pytest

from aurelix_core.capability_opportunity_bridge import CapabilityOpportunityBridge
from aurelix_core.continuous_intelligence import ContinuousIntelligence, EvidenceKind


def build_capability(validated: bool = True):
    intelligence = ContinuousIntelligence()
    objective = intelligence.propose_objective(
        domain="Engineering",
        title="Validate capability",
        question="Can the capability be demonstrated?",
    )
    evidence = intelligence.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.EXPERIMENT,
        reference="sandbox://experiment-1",
        strength=0.95,
    )
    capability = intelligence.validate_capability(
        name="validated-build-capability",
        domain="Engineering",
        required_competencies=("testing",),
        evidence_refs=(evidence.evidence_id,),
    )
    if not validated:
        intelligence.capabilities[capability.capability_id] = capability.__class__(
            capability_id=capability.capability_id,
            name=capability.name,
            domain=capability.domain,
            required_competencies=capability.required_competencies,
            evidence_refs=capability.evidence_refs,
            validated=False,
        )
    return intelligence, capability


def test_validated_capability_creates_non_executable_opportunity():
    intelligence, capability = build_capability()
    bridge = CapabilityOpportunityBridge(intelligence)

    opportunity = bridge.propose(capability.capability_id)

    assert opportunity.capability_id == capability.capability_id
    assert opportunity.status == "candidate"
    assert opportunity.requires_governor is True


def test_unvalidated_capability_cannot_create_opportunity():
    intelligence, capability = build_capability(validated=False)
    bridge = CapabilityOpportunityBridge(intelligence)

    with pytest.raises(ValueError, match="validated capabilities"):
        bridge.propose(capability.capability_id)


def test_unknown_capability_is_rejected():
    bridge = CapabilityOpportunityBridge(ContinuousIntelligence())

    with pytest.raises(KeyError):
        bridge.propose("missing-capability")


def test_projection_is_idempotent_for_same_capability():
    intelligence, capability = build_capability()
    bridge = CapabilityOpportunityBridge(intelligence)

    first = bridge.propose(capability.capability_id)
    second = bridge.propose(capability.capability_id)

    assert first.opportunity_id == second.opportunity_id
    assert len(bridge.opportunities) == 1
