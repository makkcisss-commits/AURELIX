from decimal import Decimal

import pytest

from aurelix_core.opportunities import OpportunityStage, build_opportunity


def test_opportunity_score_is_transparent_and_non_negative() -> None:
    item = build_opportunity(
        title="First revenue service",
        finding_ids=["finding-1"],
        cost_eur=Decimal("0"),
        monthly_revenue_eur=Decimal("500"),
        hours=Decimal("4"),
        complexity=2,
        risk=1,
        confidence=Decimal("0.8"),
    )
    assert item.stage is OpportunityStage.DISCOVERED
    assert item.expected_monthly_net_eur == Decimal("500")
    assert item.score > 0


def test_invalid_confidence_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_opportunity(
            title="bad",
            finding_ids=[],
            cost_eur=Decimal("0"),
            monthly_revenue_eur=Decimal("100"),
            hours=Decimal("1"),
            complexity=1,
            risk=1,
            confidence=Decimal("1.1"),
        )
