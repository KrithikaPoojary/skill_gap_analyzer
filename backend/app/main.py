"""FastAPI application factory.

This module constructs and configures the FastAPI ASGI application.  It is
separated from the entry-point (``main.py``) so that the app object can be
imported cleanly in tests without starting the server.

Day 2 additions:
- Structured logging initialised at startup.
- Global exception handlers (404 / 405 / 422 / 500) registered.
- Request timing middleware attached (X-Process-Time-Ms header).
- Correlation ID middleware attached (X-Request-ID header).
- OpenAPI metadata enriched with contact info and server list.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.timing import RequestTimingMiddleware

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Construct, configure, and return the FastAPI application instance.

    Steps performed:
    1. Initialise structured logging.
    2. Instantiate FastAPI with enriched OpenAPI metadata.
    3. Register global exception handlers.
    4. Attach middleware stack (CORS → Correlation ID → Timing).
    5. Mount the versioned API router.

    Returns:
        FastAPI: The fully configured ASGI application ready to be served.
    """
    # ── 1. Logging ────────────────────────────────────────────────────────── #
    configure_logging()

    # ── 2. FastAPI instance ───────────────────────────────────────────────── #
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "Krithika Poojary",
            "url": "https://github.com/KrithikaPoojary/skill_gap_analyzer",
        },
        openapi_tags=[
            {
                "name": "System Health",
                "description": "Liveness and readiness probes for the API server.",
            },
            {
                "name": "Jobs",
                "description": "Job postings search, filtering, and retrieval.",
            },
            {
                "name": "Matching",
                "description": "Skill-to-job matching score calculation.",
            },
            {
                "name": "Analytics",
                "description": "Market-level skill demand, salary, and trend analytics.",
            },
        ],
    )

    # ── 3. Exception handlers ─────────────────────────────────────────────── #
    register_exception_handlers(application)

    # ── 4. Middleware (outermost first) ───────────────────────────────────── #
    # CORS must be outermost so preflight OPTIONS requests are handled first.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )
    application.add_middleware(CorrelationIdMiddleware)
    application.add_middleware(RequestTimingMiddleware)
    application.add_middleware(SecurityHeadersMiddleware)

    # ── 5. Routes ─────────────────────────────────────────────────────────── #
    application.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    logger.info(
        "Application '%s' v%s ready [env=%s]",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    return application


# Module-level singleton — what Uvicorn and test clients import.
app = create_application()
