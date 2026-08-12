from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .dashboard_service import DashboardService
from .engine_factory import EngineFactory
from .http_server import PrivateReadOnlyApi, ReadOnlyRequest
from .identity import Identity, register_secret
from .intelligence_flow import IntelligenceFlow
from .system_snapshot import SystemSnapshot
from aurelix_runtime.knowledge_store import KnowledgeQuery

app = FastAPI(
    title="AURELIX Private API",
    version="0.2.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

_OWNER_ID = os.getenv("AURELIX_OWNER_ID", "owner")
_OWNER_SECRET = os.getenv("AURELIX_OWNER_SECRET")
_identity = Identity(_OWNER_ID, "owner")
_credential = register_secret(_OWNER_ID, _OWNER_SECRET) if _OWNER_SECRET else None
_factory_error: str | None = None

try:
    _factory = EngineFactory()
    _runtime = _factory.runtime
    _flow = IntelligenceFlow(_factory)
except Exception as exc:
    _factory = None
    _runtime = None
    _flow = None
    _factory_error = type(exc).__name__


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class ExperimentExecutionRequest(BaseModel):
    observations: list[dict[str, Any]] = Field(default_factory=list)


def _live_snapshot() -> dict:
    if _factory is None or _runtime is None:
        return {
            **SystemSnapshot(system="DEGRADED").public(),
            "error": "runtime_initialization_failed",
            "error_type": _factory_error,
        }

    runtime_status = _runtime.store.status()
    experiments = _runtime.query_experiments()
    recent_knowledge = _factory.knowledge.search(KnowledgeQuery("", limit=10))
    return {
        **SystemSnapshot().public(),
        "runtime": runtime_status,
        "providers": {
            "model_configured": _factory.model_provider is not None,
            "research_configured": _factory.research_provider is not None,
            "knowledge_backend": type(_factory.knowledge).__name__,
        },
        "experiments": {
            "total": len(experiments),
            "active": len([x for x in experiments if x["status"] in {"proposed", "running", "measuring", "evaluation"}]),
            "completed": len([x for x in experiments if x["status"] == "complete"]),
        },
        "knowledge": {
            "total_items": _factory.knowledge.count(),
            "recent": [
                {"id": item.id, "title": item.title, "tags": item.tags, "created_at": item.created_at}
                for item in recent_knowledge
            ],
        },
        "audit_events": _runtime.store.audit_summary(20)["recent"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _experiments(status_filter: str | None):
    return _runtime.query_experiments(status_filter) if _runtime is not None else []


def _knowledge(query: str, limit: int):
    if _factory is None:
        return []
    return [
        {"id": item.id, "title": item.title, "content": item.content, "tags": item.tags, "created_at": item.created_at}
        for item in _factory.knowledge.search(KnowledgeQuery(query, limit=limit))
    ]


def _audit(limit: int):
    return _runtime.store.audit_summary(limit)["recent"] if _runtime is not None else []


_api = PrivateReadOnlyApi(
    DashboardService(snapshot_provider=_live_snapshot),
    experiments=_experiments,
    knowledge=_knowledge,
    audit=_audit,
)


def require_owner(x_aurelix_secret: str | None = Header(default=None)) -> ReadOnlyRequest:
    if _credential is None or x_aurelix_secret is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication_required")
    return ReadOnlyRequest(_identity, _credential, x_aurelix_secret)


@app.get("/health", include_in_schema=False)
def health():
    response = _api.get_health()
    return response.body


@app.get("/ready", include_in_schema=False)
def ready():
    service_ready = _OWNER_SECRET is not None and _factory is not None and _runtime is not None
    response = _api.get_readiness(service_ready)
    if response.status != 200:
        raise HTTPException(status_code=response.status, detail=response.body["status"])
    return response.body


@app.get("/v1/control/snapshot")
def snapshot(request: ReadOnlyRequest = Depends(require_owner)):
    response = _api.get_snapshot(request)
    if response.status != 200:
        raise HTTPException(status_code=response.status, detail=response.body["error"])
    return response.body


@app.get("/v1/control/experiments")
def experiments(status_filter: str | None = Query(default=None, alias="status"), request: ReadOnlyRequest = Depends(require_owner)):
    response = _api.get_experiments(request, status_filter)
    if response.status != 200:
        raise HTTPException(status_code=response.status, detail=response.body["error"])
    return response.body


@app.get("/v1/control/knowledge")
def knowledge(q: str = "", limit: int = 20, request: ReadOnlyRequest = Depends(require_owner)):
    response = _api.get_knowledge(request, q, limit)
    if response.status != 200:
        raise HTTPException(status_code=response.status, detail=response.body["error"])
    return response.body


@app.get("/v1/control/audit")
def audit(limit: int = 50, request: ReadOnlyRequest = Depends(require_owner)):
    response = _api.get_audit(request, limit)
    if response.status != 200:
        raise HTTPException(status_code=response.status, detail=response.body["error"])
    return response.body


@app.post("/v1/actions/research")
def research_action(payload: ResearchRequest, request: ReadOnlyRequest = Depends(require_owner)):
    if _flow is None or _factory is None:
        raise HTTPException(status_code=503, detail="runtime_unavailable")
    if _factory.research_provider is None:
        raise HTTPException(status_code=503, detail="research_provider_not_configured")
    try:
        return _flow.research_to_experiment(payload.query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"research_flow_failed: {type(exc).__name__}") from exc


@app.post("/v1/actions/experiments/{experiment_id}/execute")
def execute_experiment(
    experiment_id: str,
    payload: ExperimentExecutionRequest,
    request: ReadOnlyRequest = Depends(require_owner),
):
    if _flow is None:
        raise HTTPException(status_code=503, detail="runtime_unavailable")
    try:
        return _flow.execute_experiment(experiment_id, payload.observations)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"experiment_execution_failed: {type(exc).__name__}") from exc


_WEB_ROOT = Path(__file__).resolve().parents[2] / "web"
if _WEB_ROOT.is_dir():
    app.mount("/", StaticFiles(directory=_WEB_ROOT, html=True), name="web")


def main() -> None:
    import uvicorn

    uvicorn.run(
        "aurelix_core.server:app",
        host=os.getenv("AURELIX_HOST", "127.0.0.1"),
        port=int(os.getenv("AURELIX_PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()
