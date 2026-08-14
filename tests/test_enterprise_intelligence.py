from decimal import Decimal

import pytest

from aurelix_core.enterprise_intelligence import (
    AssetKind,
    EnterpriseRegistry,
    ProfileKind,
)


def test_profile_is_rooted_in_identity_and_assets_belong_to_profile():
    registry = EnterpriseRegistry()
    profile = registry.create_profile(
        identity_id="identity-001",
        name="AURELIX Enterprise",
        kind=ProfileKind.BUSINESS,
    )

    asset = registry.register_asset(
        profile_id=profile.profile_id,
        name="Content Channel",
        kind=AssetKind.CHANNEL,
        scope="sponsor-content",
        estimated_value_eur=Decimal("250"),
    )

    assert profile.identity_id == "identity-001"
    assert registry.profiles[profile.profile_id] == profile
    assert asset.profile_id == profile.profile_id
    assert asset.estimated_value_eur == Decimal("250")


def test_assets_cannot_cross_profile_boundaries():
    registry = EnterpriseRegistry()
    first = registry.create_profile(identity_id="identity-a", name="First")
    second = registry.create_profile(identity_id="identity-b", name="Second")
    asset = registry.register_asset(
        profile_id=first.profile_id,
        name="Private dataset",
        kind=AssetKind.DATA,
        scope="internal",
    )

    with pytest.raises(ValueError, match="does not belong to profile"):
        registry.link(profile_id=second.profile_id, asset_ids=(asset.asset_id,), knowledge_refs=("k-1",))


def test_competency_and_link_connect_learning_to_downstream_business_context():
    registry = EnterpriseRegistry()
    profile = registry.create_profile(identity_id="identity-003", name="Enterprise")
    asset = registry.register_asset(
        profile_id=profile.profile_id,
        name="Production workflow",
        kind=AssetKind.CAPABILITY,
        scope="controlled",
    )
    competency = registry.register_competency(
        profile_id=profile.profile_id,
        domain="creative-commerce",
        name="content-production",
        level=0.9,
        confidence=0.85,
        knowledge_refs=("knowledge-1",),
        learning_refs=("objective-1",),
    )

    link = registry.link(
        profile_id=profile.profile_id,
        asset_ids=(asset.asset_id,),
        competency_ids=(competency.competency_id,),
        knowledge_refs=("knowledge-1",),
        learning_refs=("objective-1",),
        opportunity_id="opportunity-1",
        runtime_execution_id="execution-1",
        revenue_source_id="revenue-1",
    )

    assert link.asset_ids == (asset.asset_id,)
    assert link.competency_ids == (competency.competency_id,)
    assert link.opportunity_id == "opportunity-1"
    assert link.runtime_execution_id == "execution-1"
    assert link.revenue_source_id == "revenue-1"


def test_invalid_enterprise_context_is_rejected():
    registry = EnterpriseRegistry()

    with pytest.raises(ValueError):
        registry.create_profile(identity_id="", name="Invalid")

    with pytest.raises(KeyError):
        registry.register_asset(
            profile_id="missing",
            name="Asset",
            kind=AssetKind.DIGITAL,
            scope="test",
        )

    profile = registry.create_profile(identity_id="identity-004", name="Valid")
    with pytest.raises(ValueError, match="negative"):
        registry.register_asset(
            profile_id=profile.profile_id,
            name="Invalid value",
            kind=AssetKind.PRODUCT,
            scope="test",
            estimated_value_eur=Decimal("-1"),
        )
