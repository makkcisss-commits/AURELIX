from decimal import Decimal

import pytest

from aurelix_core.budget import Budget, BudgetExceeded


def test_budget_authorizes_within_limit() -> None:
    budget = Budget.create("EUR", "100")
    budget.consume("25.50")
    assert budget.spent == Decimal("25.50")
    assert budget.remaining == Decimal("74.50")


def test_budget_rejects_over_limit_without_consuming() -> None:
    budget = Budget.create("EUR", "100")
    with pytest.raises(BudgetExceeded):
        budget.consume("100.01")
    assert budget.spent == Decimal("0")


def test_budget_rejects_negative_values() -> None:
    with pytest.raises(ValueError):
        Budget.create("EUR", "-1")
    budget = Budget.create("EUR", "100")
    with pytest.raises(ValueError):
        budget.consume("-1")


def test_budget_uses_decimal_for_money() -> None:
    budget = Budget.create("EUR", "0.30")
    budget.consume("0.10")
    budget.consume("0.20")
    assert budget.remaining == Decimal("0.00")
