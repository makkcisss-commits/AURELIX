from aurelix_core.capability_control_plane import (
    CapabilityControlPlane,
    CapabilityProvider,
    CapabilityStatus,
    ProviderKind,
)


def provider(provider_id: str, **kwargs) -> CapabilityProvider:
    return CapabilityProvider(provider_id, "Data_Analysis", ProviderKind.AGENT, **kwargs)


def test_missing_capability_is_explicit():
    plane = CapabilityControlPlane()
    result = plane.resolve("data_analysis")
    assert result.status is CapabilityStatus.MISSING
    assert result.providers == ()


def test_unauthorized_provider_cannot_be_selected():
    plane = CapabilityControlPlane()
    plane.register(provider("agent-a", authorized=False))
    result = plane.resolve("data-analysis")
    assert result.status is CapabilityStatus.UNAUTHORIZED


def test_unavailable_provider_cannot_be_selected():
    plane = CapabilityControlPlane()
    plane.register(provider("agent-a", available=False))
    result = plane.resolve("data-analysis")
    assert result.status is CapabilityStatus.UNAVAILABLE


def test_disabled_provider_does_not_hide_missing_capability():
    plane = CapabilityControlPlane()
    plane.register(provider("agent-a", enabled=False))
    result = plane.resolve("data-analysis")
    assert result.status is CapabilityStatus.BLOCKED


def test_selection_is_deterministic_and_priority_aware():
    plane = CapabilityControlPlane()
    plane.register(provider("low", priority=1))
    plane.register(provider("high", priority=10))
    assert plane.select("data_analysis").provider_id == "high"
