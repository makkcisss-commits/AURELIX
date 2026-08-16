from __future__ import annotations

from aurelix_core.server import app


EXPECTED_PUBLIC_ROUTES = {
    ("GET", "/"),
    ("GET", "/health"),
    ("GET", "/ready"),
    ("GET", "/v1/control/snapshot"),
    ("GET", "/v1/control/autonomy"),
    ("GET", "/v1/control/diagnostics"),
    ("GET", "/v1/control/validation"),
    ("GET", "/v1/control/experiments"),
    ("GET", "/v1/control/knowledge"),
    ("GET", "/v1/control/audit"),
    ("POST", "/v1/actions/research"),
    ("POST", "/v1/actions/experiments/{experiment_id}/execute"),
    ("POST", "/v1/actions/objectives"),
    ("POST", "/v1/actions/economic/outcomes"),
}


def _route_contracts() -> set[tuple[str, str]]:
    routes: set[tuple[str, str]] = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", set())
        if path:
            for method in methods:
                routes.add((method, path))
    return routes


def test_existing_public_api_routes_are_preserved() -> None:
    routes = _route_contracts()
    assert EXPECTED_PUBLIC_ROUTES <= routes


def test_sensitive_routes_remain_dependency_protected() -> None:
    protected_prefixes = ("/v1/control/", "/v1/actions/")
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith(protected_prefixes):
            continue
        assert getattr(route, "dependant", None) is not None
        dependency_names = {
            getattr(dependency.call, "__name__", "")
            for dependency in route.dependant.dependencies
        }
        assert "require_owner" in dependency_names, path


def test_new_routes_must_not_silently_replace_existing_contracts() -> None:
    routes = _route_contracts()
    assert not {item for item in EXPECTED_PUBLIC_ROUTES if item not in routes}
