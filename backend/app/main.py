"""FastAPI application factory.

This module constructs and configures the FastAPI ASGI application.  It is
separated from the entry-point (``main.py``) so that the app object can be
imported cleanly in tests without starting the server.

Design principles applied here:
- Application factory pattern (``create_application()``) keeps configuration
  centralized and allows dependency injection in tests.
- All external configuration originates from ``app.core.config.settings``.
- Route registration is delegated to the versioned API router.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings


def create_application() -> FastAPI:
    """Construct, configure, and return the FastAPI application instance.

    Steps performed:
    1. Instantiate FastAPI with metadata sourced from ``settings``.
    2. Register CORS middleware with origins from ``settings``.
    3. Mount the versioned API router.

    Returns:
        FastAPI: The fully configured ASGI application ready to be served.
    """
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------ #
    # Middleware
    # ------------------------------------------------------------------ #
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------ #
    # Route Registration
    # ------------------------------------------------------------------ #
    application.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return application


# The module-level ``app`` instance is what Uvicorn (and test clients) import.
app = create_application()
