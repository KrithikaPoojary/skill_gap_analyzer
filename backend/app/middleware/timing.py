"""Request timing middleware.

Measures the wall-clock duration of every HTTP request and appends two
custom headers to the response:

- ``X-Process-Time-Ms``  — elapsed time in milliseconds (float, 2 dp)
- ``X-Process-Time-S``   — elapsed time in seconds (float, 6 dp)

These headers are useful for:
- Performance profiling in development
- SLA monitoring in staging/production
- Frontend devtools network inspection

Usage: registered in ``create_application()`` via
``app.add_middleware(RequestTimingMiddleware)``.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that measures and exposes per-request processing time."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Wrap request processing with a high-resolution timer.

        Args:
            request:   The incoming Starlette/FastAPI request.
            call_next: The next middleware or route handler in the chain.

        Returns:
            Response: The original response augmented with timing headers.
        """
        start_time = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_seconds = time.perf_counter() - start_time
        elapsed_ms = elapsed_seconds * 1_000

        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        response.headers["X-Process-Time-S"] = f"{elapsed_seconds:.6f}"

        logger.debug(
            "%s %s completed in %.2f ms (status=%s)",
            request.method,
            request.url.path,
            elapsed_ms,
            response.status_code,
        )

        return response
