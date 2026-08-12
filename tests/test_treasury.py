from decimal import Decimal
import pytest

from aurelix_core.treasury import Treasury


def test_zero_start_is_supported() -> None:
    treasury = Treasury()
    snapshot = treasury.snapshot()
    assert snapshot.free_eur == Decimal("0")


def test_reservation_requires_available_funds() -> None:
    treasury = Treasury(Decimal("100"))
    assert treasury.can_reserve(Decimal("40"))
    treasury.reserve(Decimal("40"))
    assert treasury.snapshot().free_eur == Decimal("60")


def test_reservation_above_free_balance_is_blocked() -> None:
    treasury = Treasury(Decimal("100"))
    treasury.reserve(Decimal("80"))
    assert not treasury.can_reserve(Decimal("30"))
    with pytest.raises(ValueError):
        treasury.reserve(Decimal("30"))
