from pathlib import Path

import yaml

from aurelix_core.server import app


CONTRACT_PATH = Path(__file__).resolve().parents[1] / "openapi" / "aurelix.openapi.yaml"


def _contract() -> dict:
    with CONTRACT_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _app_api_routes() -> dict[str, set[str]]:
    routes: dict[str, set[str]] = {}
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set())
        if not path or not methods:
            continue
        if path in {"/health", "/ready"} or path.startswith("/v1/"):
            routes[path] = {method.lower() for method in methods}
    return routes


def test_openapi_contract_covers_all_control_and_action_routes() -> None:
    contract = _contract()
    contract_routes = {
        path: set(operation for operation in definition if operation in {"get", "post", "put", "patch", "delete"})
        for path, definition in contract["paths"].items()
    }
    assert contract_routes == _app_api_routes()


def test_private_routes_require_the_declared_secret_scheme() -> None:
    contract = _contract()
    scheme = contract["components"]["securitySchemes"]["AurelixSecret"]
    assert scheme["type"] == "apiKey"
    assert scheme["in"] == "header"
    assert scheme["name"] == "X-AURELIX-SECRET"

    assert contract["paths"]["/health"]["get"]["security"] == []
    assert contract["paths"]["/ready"]["get"]["security"] == []

    for path, definition in contract["paths"].items():
        if path.startswith("/v1/"):
            for operation in definition.values():
                assert operation["security"] == [{"AurelixSecret": []}]


def test_contract_does_not_expose_fastapi_runtime_openapi() -> None:
    assert app.openapi_url is None
    assert app.docs_url is None
    assert app.redoc_url is None
