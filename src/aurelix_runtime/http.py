from __future__ import annotations

import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable


class PrivateControlHandler(BaseHTTPRequestHandler):
    runtime = None
    token = ""

    def _authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        return hmac.compare_digest(supplied, f"Bearer {self.token}") if self.token else False

    def _json(self, status: int, body: dict) -> None:
        raw = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        if not self._authorized(): return self._json(401, {"error": "unauthorized"})
        if self.path == "/health": return self._json(200, {"status": "ok"})
        if self.path == "/api/v1/control/runtime": return self._json(200, self.runtime.store.status())
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        # No mutation endpoints are exposed by this V1 private read-only server.
        if not self._authorized(): return self._json(401, {"error": "unauthorized"})
        self._json(405, {"error": "method_not_allowed"})


def serve_private_control(runtime, host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    """Bind a private read-only control endpoint. TLS should terminate at the deployment edge."""
    PrivateControlHandler.runtime = runtime
    PrivateControlHandler.token = os.environ.get("AURELIX_CONTROL_TOKEN", "")
    if not PrivateControlHandler.token:
        raise RuntimeError("AURELIX_CONTROL_TOKEN is required")
    server = ThreadingHTTPServer((host or "127.0.0.1", port or 8080), PrivateControlHandler)
    return server
