from __future__ import annotations

from fastapi.responses import HTMLResponse


def render_dashboard() -> HTMLResponse:
    """Return the minimal live surface for the private AURELIX service."""
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AURELIX</title></head>
<body><main><h1>AURELIX</h1><p>Private control surface</p></main></body>
</html>"""
    )
