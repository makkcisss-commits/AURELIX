from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class BudgetExceeded(Exception):
    """Raised when an operation would exceed its authorized budget."""


@dataclass
class Budget:
    currency: str
    limit: Decimal
    spent: Decimal = Decimal("0")

    @classmethod
    def create(cls, currency: str, limit: str | Decimal) -> "Budget":
        try:
            value = Decimal(str(limit))
        except InvalidOperation as exc:
            raise ValueError("invalid budget limit") from exc
        if value < 0:
            raise ValueError("budget limit cannot be negative")
        return cls(currency=currency, limit=value)

    @property
    def remaining(self) -> Decimal:
        return self.limit - self.spent

    def authorize(self, amount: str | Decimal) -> None:
        try:
            value = Decimal(str(amount))
        except InvalidOperation as exc:
            raise ValueError("invalid budget amount") from exc
        if value < 0:
            raise ValueError("budget amount cannot be negative")
        if value > self.remaining:
            raise BudgetExceeded(
                f"budget exceeded: requested={value} remaining={self.remaining}"
            )

    def consume(self, amount: str | Decimal) -> "Budget":
        self.authorize(amount)
        value = Decimal(str(amount))
        self.spent += value
        return self
