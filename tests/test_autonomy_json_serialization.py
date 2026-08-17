from decimal import Decimal

from aurelix_runtime.autonomy_fabric import _jsonable


def test_jsonable_serializes_decimal_as_exact_decimal_text():
    payload = {"amount": Decimal("123.4500"), "nested": [Decimal("0.0100")]}

    assert _jsonable(payload) == {
        "amount": "123.4500",
        "nested": ["0.0100"],
    }
