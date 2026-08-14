from decimal import Decimal

import pytest

from aurelix_core.opportunity_revenue_bridge import OpportunityRevenueBridge


def test_productive_revenue_requires_external_reference():
    bridge = OpportunityRevenueBridge()
    # No source admission is needed to verify the fail-closed API contract.
    with pytest.raises(KeyError):
        bridge.record_observation("missing-source", Decimal("1"))


def test_synthetic_observation_never_becomes_productive():
    from tests.test_opportunity_revenue_bridge import approved_opportunity, qualification_for
    opportunity = approved_opportunity()
    bridge = OpportunityRevenueBridge()
    source = bridge.admit(opportunity, qualification=qualification_for(opportunity), owner_role="business", channel="test")
    updated = bridge.record_observation(source.source_id, Decimal("10"), synthetic=True)
    assert updated.is_productive is False
    assert updated.observed_daily_eur == Decimal("0")
