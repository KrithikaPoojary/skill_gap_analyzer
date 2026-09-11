"""Health check endpoint router.

Provides ``GET /api/v1/health`` and ``GET /api/v1/health/db`` endpoints
confirming API server liveness, application metadata, and database connectivity,
all wrapped in the standard ``APIResponse`` envelope.
"""

from datetime import datetime, timezone
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings
from app.db.session import ping_database
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
    """Return application liveness status wrapped in the APIResponse envelope."""
    payload = {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": "connected" if ping_database() else "unavailable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(content=ok(data=payload).model_dump())


@router.get(
    "/db",
    summary="Database Connectivity Health Check",
    description="Executes a live query against the database engine to verify read/write readiness.",
    response_description="Detailed database latency and dialect health check.",
)
def database_health_check(db: DbSession) -> JSONResponse:
    """Check database connection and measure roundtrip query latency."""
    start_time = time.perf_counter()
    db.execute(text("SELECT 1"))
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    payload = {
        "status": "healthy",
        "database": "connected",
        "latency_ms": latency_ms,
        "dialect": db.bind.dialect.name if db.bind else "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(content=ok(data=payload).model_dump())
