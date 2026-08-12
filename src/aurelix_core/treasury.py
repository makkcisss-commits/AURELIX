from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from threading import Lock


@dataclass(frozen=True)
class TreasurySnapshot:
    available_eur: Decimal
    reserved_eur: Decimal
    spent_eur: Decimal

    @property
    def free_eur(self) -> Decimal:
        return self.available_eur - self.reserved_eur


class Treasury:
    """Read-first financial state; no payment execution is implemented here."""

    def __init__(self, initial_eur: Decimal = Decimal("0")) -> None:
        if initial_eur < 0:
            raise ValueError("initial balance cannot be negative")
        self._available = initial_eur
        self._reserved = Decimal("0")
        self._spent = Decimal("0")
        self._lock = Lock()

    def snapshot(self) -> TreasurySnapshot:
        with self._lock:
            return TreasurySnapshot(self._available, self._reserved, self._spent)

    def can_reserve(self, amount_eur: Decimal) -> bool:
        if amount_eur <= 0:
            return False
        with self._lock:
            return amount_eur <= self._available - self._reserved

    def reserve(self, amount_eur: Decimal) -> TreasurySnapshot:
        if amount_eur <= 0:
            raise ValueError("reservation must be positive")
        with self._lock:
            if amount_eur > self._available - self._reserved:
                raise ValueError("insufficient available treasury")
            self._reserved += amount_eur
            return TreasurySnapshot(self._available, self._reserved, self._spent)
