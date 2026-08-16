from aurelix_core.capability_control_plane import (
    CapabilityControlPlane,
    CapabilityProvider,
    CapabilityState,
)


def test_unknown_capability_is_explicitly_missing() -> None:
    plane = CapabilityControlPlane()
    result = plane.resolve("Power BI")
    assert result.state is CapabilityState.MISSING
    assert result.reason == "capability is not registered"


def test_registered_capability_without_provider_requires_learning() -> None:
    plane = CapabilityControlPlane()
    plane.register_capability("Power BI")
    result = plane.resolve("power bi")
    assert result.state is CapabilityState.LEARNING_REQUIRED


def test_authorization_and_availability_are_distinct() -> None:
    plane = CapabilityControlPlane()
    plane.register_provider(
        CapabilityProvider(
            provider_id="powerbi-agent",
            provider_type="agent",
            capabilities=frozenset({"power bi"}),
            enabled=False,
            authorized=True,
        )
    )
    result = plane.resolve("Power BI")
    assert result.state is CapabilityState.UNAVAILABLE

    plane.register_provider(
        CapabilityProvider(
            provider_id="powerbi-service",
            provider_type="service",
            capabilities=frozenset({"power bi"}),
            enabled=True,
            authorized=False,
        )
    )
    result = plane.resolve("Power BI")
    assert result.state is CapabilityState.UNAVAILABLE


def test_resolved_capability_returns_only_authorized_enabled_providers() -> None:
    plane = CapabilityControlPlane()
    plane.register_providers(
        [
            CapabilityProvider("agent-a", "agent", frozenset({"sql"})),
            CapabilityProvider("tool-b", "tool", frozenset({"sql"}), enabled=False),
            CapabilityProvider("service-c", "service", frozenset({"sql"}), authorized=False),
        ]
    )
    result = plane.resolve("SQL")
    assert result.state is CapabilityState.RESOLVED
    assert [provider.provider_id for provider in result.providers] == ["agent-a"]
