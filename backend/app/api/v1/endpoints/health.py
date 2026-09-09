"""Health check endpoint router.

Provides a lightweight ``GET /api/v1/health`` endpoint that confirms the
API server is reachable and returns basic application metadata wrapped in
the standard ``APIResponse`` envelope.

Day 2: Response now uses the ``ok()`` envelope so it is consistent with
all other successful API responses.
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.response import ok

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get(
    "",
    summary="Application Health Check",
    description=(
        "Returns HTTP 200 with application metadata when the server is running. "
        "Response is wrapped in the standard APIResponse envelope. "
        "Used as a liveness probe in CI pipelines and deployment health checks."
    ),
    response_description="Success envelope containing status, app metadata, and UTC timestamp.",
)
def health_check() -> JSONResponse:
    """Return application liveness status wrapped in the APIResponse envelope.

    Returns:
        JSONResponse: JSON payload containing success flag, app name, version,
                      environment label, and the current UTC timestamp.
    """
    payload = {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(content=ok(data=payload).model_dump())
