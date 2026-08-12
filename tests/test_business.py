from decimal import Decimal

import pytest

from aurelix_core.business import BusinessStage, create_activity


def test_activity_starts_as_idea_and_tracks_margin() -> None:
    item = create_activity(
        name="Internal SaaS",
        channel="saas",
        description="Private software product",
        monthly_revenue_eur=Decimal("500"),
        monthly_cost_eur=Decimal("100"),
    )
    assert item.stage is BusinessStage.IDEA
    assert item.monthly_margin_eur == Decimal("400")


def test_negative_financial_values_are_rejected() -> None:
    with pytest.raises(ValueError):
        create_activity(
            name="Bad", channel="service", description="x",
            monthly_revenue_eur=Decimal("-1"),
        )
