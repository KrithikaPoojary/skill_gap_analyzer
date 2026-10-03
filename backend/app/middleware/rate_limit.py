"""Rate limiting ASGI middleware using in-memory sliding window."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding window rate limiter per client IP."""

    def __init__(
        self,
        app,
        max_requests: int = 120,
        window_seconds: int = 60,
        exempt_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exempt_paths = exempt_paths or {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/health/ready",
            "/api/v1/health/live",
        }
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check exemption
        if any(request.url.path.startswith(p) for p in self.exempt_paths):
            return await call_next(request)

        # Determine client identifier
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")

        now = time.time()
        window_start = now - self.window_seconds

        # Prune older timestamps
        timestamps = [ts for ts in self._requests[client_ip] if ts > window_start]
        self._requests[client_ip] = timestamps

        if len(timestamps) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Rate limit exceeded."},
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._requests[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - len(self._requests[client_ip])))
        return response
