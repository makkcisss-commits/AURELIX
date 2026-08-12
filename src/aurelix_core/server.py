from __future__ import annotations

import os

from fastapi import Depends, FastAPI, Header, HTTPException, status

from .dashboard_service import DashboardService
from .http_server import PrivateReadOnlyApi, ReadOnlyRequest
from .identity import Identity, register_secret
from .system_snapshot import SystemSnapshot

app = FastAPI(
    title="AURELIX Private API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Development bootstrap only. Production credentials must come from a real
# secret manager and never from source control or a public environment dump.
_OWNER_ID = os.getenv("AURELIX_OWNER_ID", "owner")
_OWNER_SECRET = os.getenv("AURELIX_OWNER_SECRET")
_identity = Identity(_OWNER_ID, "owner")
_credential = register_secret(_OWNER_ID, _OWNER_SECRET) if _OWNER_SECRET else None
_api = PrivateReadOnlyApi(DashboardService(SystemSnapshot()))


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
    response = _api.get_readiness(_OWNER_SECRET is not None)
    if response.status != 200:
        raise HTTPException(status_code=response.status, detail=response.body["status"])
    return response.body


@app.get("/v1/control/snapshot")
def snapshot(request: ReadOnlyRequest = Depends(require_owner)):
    response = _api.get_snapshot(request)
    if response.status != 200:
        raise HTTPException(status_code=response.status, detail=response.body["error"])
    return response.body
