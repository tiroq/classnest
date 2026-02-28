"""Basic Auth middleware for the admin panel."""

from __future__ import annotations

import base64
import secrets

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Protect all /admin routes with HTTP Basic Auth."""

    def __init__(self, app, username: str, password: str) -> None:
        super().__init__(app)
        self._username = username
        self._password = password

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/admin/health":
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not self._is_valid(auth):
            return Response(
                content="Unauthorized",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="ClassNest Admin"'},
            )
        return await call_next(request)

    def _is_valid(self, auth_header: str) -> bool:
        if not auth_header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(auth_header[6:]).decode()
            username, _, password = decoded.partition(":")
            return secrets.compare_digest(username, self._username) and secrets.compare_digest(
                password, self._password
            )
        except Exception:
            return False
