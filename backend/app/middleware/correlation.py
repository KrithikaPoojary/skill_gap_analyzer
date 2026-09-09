"""Correlation ID middleware.

Attaches a unique request identifier to every HTTP request/response cycle.
This ID can be used to correlate log lines across distributed services or
to track a specific request through the system.

Behaviour:
- If the client sends an ``X-Request-ID`` header, that value is reused.
- Otherwise, a new UUID4 is generated and used as the correlation ID.
- The ID is always echoed back in the ``X-Request-ID`` response header.
- The ID is stored in a ``ContextVar`` so it can be retrieved inside any
  log formatter or service function without passing it explicitly.

Usage: registered in ``create_application()`` via
``app.add_middleware(CorrelationIdMiddleware)``.
"""

import logging
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Thread-safe storage for the current request's correlation ID.
# Accessible anywhere: ``from app.middleware.correlation import request_id_var``
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

REQUEST_ID_HEADER = "X-Request-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that manages per-request correlation identifiers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Extract or generate a correlation ID and propagate it.

        Args:
            request:   The incoming Starlette/FastAPI request.
            call_next: The next middleware or route handler in the chain.

        Returns:
            Response: The original response with the ``X-Request-ID`` header set.
        """
        # Honour a client-supplied ID; otherwise generate a fresh one.
        correlation_id: str = (
            request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        )

        # Store in context so loggers and service code can access it.
        token = request_id_var.set(correlation_id)

        try:
            response: Response = await call_next(request)
        finally:
            # Always reset context to avoid leakage across concurrent requests.
            request_id_var.reset(token)

        response.headers[REQUEST_ID_HEADER] = correlation_id
        return response
