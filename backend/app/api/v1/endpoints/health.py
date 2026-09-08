"""Health check endpoint router.

Provides a lightweight ``GET /api/v1/health`` endpoint that confirms the
API server is reachable and returns basic application metadata.  This is
the canonical liveness check for load balancers, CI pipelines, and
developer smoke tests.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get(
    "",
    summary="Application Health Check",
    description=(
        "Returns HTTP 200 with application metadata when the server is running. "
        "Used as a liveness probe in CI pipelines and deployment health checks."
    ),
    response_description="Health status payload containing app name, version, and server timestamp.",
)
def health_check() -> dict:
    """Return application liveness status and metadata.

    Returns:
        dict: A JSON payload containing status, application name, version,
              environment label, and the current UTC timestamp.
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
