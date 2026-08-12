import pytest

from aurelix_api.auth import AuthenticatedPrincipal
from aurelix_api.read_only import ReadOnlyControlAPI
from aurelix_core.control_center import ControlCenter
from aurelix_core.governor import Governor
from aurelix_core.revenue import RevenueEngine
from aurelix_core.treasury import Treasury


def api() -> ReadOnlyControlAPI:
    return ReadOnlyControlAPI(
        ControlCenter(treasury=Treasury(), revenue=RevenueEngine(), governor=Governor())
    )


def test_read_endpoint_requires_scope() -> None:
    with pytest.raises(PermissionError):
        api().get_snapshot(AuthenticatedPrincipal("owner", frozenset()))


def test_read_endpoint_returns_snapshot() -> None:
    result = api().get_snapshot(
        AuthenticatedPrincipal("owner", frozenset({"control:read"}))
    )
    assert "system" in result
    assert "components" in result
