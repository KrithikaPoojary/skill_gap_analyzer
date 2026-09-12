"""API Version 1 router aggregator.

All v1 endpoint routers are registered here.  The main application mounts
this router under the ``/api/v1`` prefix defined in ``settings.api_v1_prefix``.

Adding a new feature area:
1. Create ``endpoints/<feature>.py`` with its ``APIRouter``.
2. Import the router here and add an ``include_router`` call.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.jobs import router as jobs_router

api_v1_router = APIRouter()

# ---------------------------------------------------------------------- #
# Register all v1 endpoint routers
# ---------------------------------------------------------------------- #
api_v1_router.include_router(health_router)
api_v1_router.include_router(jobs_router)
