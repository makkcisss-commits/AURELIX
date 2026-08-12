import pytest

from aurelix_core.resource_scope import (
    ResourceKind,
    ResourcePermission,
    ResourceRequest,
    ScopeDenied,
    authorize_resource,
)


def test_scoped_permission_allows_exact_target() -> None:
    permission = ResourcePermission(
        actor_id="research-agent",
        resource=ResourceKind.RESEARCH,
        operations=frozenset({"read"}),
        scope="project-alpha",
    )
    authorize_resource(
        ResourceRequest("research-agent", ResourceKind.RESEARCH, "read", "project-alpha"),
        permission,
    )


def test_wrong_actor_is_denied() -> None:
    permission = ResourcePermission(
        actor_id="research-agent",
        resource=ResourceKind.RESEARCH,
        operations=frozenset({"read"}),
        scope="project-alpha",
    )
    with pytest.raises(ScopeDenied):
        authorize_resource(
            ResourceRequest("other-agent", ResourceKind.RESEARCH, "read", "project-alpha"),
            permission,
        )


def test_wrong_resource_is_denied() -> None:
    permission = ResourcePermission(
        actor_id="research-agent",
        resource=ResourceKind.RESEARCH,
        operations=frozenset({"read"}),
        scope="project-alpha",
    )
    with pytest.raises(ScopeDenied):
        authorize_resource(
            ResourceRequest("research-agent", ResourceKind.TREASURY, "read", "project-alpha"),
            permission,
        )


def test_wrong_operation_is_denied() -> None:
    permission = ResourcePermission(
        actor_id="research-agent",
        resource=ResourceKind.RESEARCH,
        operations=frozenset({"read"}),
        scope="project-alpha",
    )
    with pytest.raises(ScopeDenied):
        authorize_resource(
            ResourceRequest("research-agent", ResourceKind.RESEARCH, "write", "project-alpha"),
            permission,
        )


def test_wrong_scope_is_denied() -> None:
    permission = ResourcePermission(
        actor_id="research-agent",
        resource=ResourceKind.RESEARCH,
        operations=frozenset({"read"}),
        scope="project-alpha",
    )
    with pytest.raises(ScopeDenied):
        authorize_resource(
            ResourceRequest("research-agent", ResourceKind.RESEARCH, "read", "project-beta"),
            permission,
        )
