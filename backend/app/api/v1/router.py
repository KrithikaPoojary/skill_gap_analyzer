"""API Version 1 router aggregator.

All v1 endpoint routers are registered here.  The main application mounts
this router under the ``/api/v1`` prefix defined in ``settings.api_v1_prefix``.

Adding a new feature area:
1. Create ``endpoints/<feature>.py`` with its ``APIRouter``.
2. Import the router here and add an ``include_router`` call.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.gap_analysis import router as gap_analysis_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.job_matching import router as job_matching_router
from app.api.v1.endpoints.jobs import router as jobs_router
from app.api.v1.endpoints.profile import router as profile_router
from app.api.v1.endpoints.recommendations import router as recommendations_router
from app.api.v1.endpoints.resume import router as resume_router
from app.api.v1.endpoints.roadmaps import router as roadmaps_router
from app.api.v1.endpoints.skills import router as skills_router

api_v1_router = APIRouter()

# ---------------------------------------------------------------------- #
# Register all v1 endpoint routers
# ---------------------------------------------------------------------- #
api_v1_router.include_router(auth_router)
api_v1_router.include_router(health_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(job_matching_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(skills_router)
api_v1_router.include_router(profile_router)
api_v1_router.include_router(gap_analysis_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(roadmaps_router)
api_v1_router.include_router(resume_router)
