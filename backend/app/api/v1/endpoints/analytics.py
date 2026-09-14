"""Market intelligence and skill gap analytics REST API endpoints."""

from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.models.skill import SkillCategory
from app.schemas.response import ok
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Market Analytics"])


@router.get(
    "/overview",
    summary="Executive market overview summary",
    response_model=dict,
)
def get_market_overview(db: DbSession) -> dict[str, Any]:
    """Retrieve macro-level market KPIs, top skills, roles, and remote employment ratios."""
    overview = analytics_service.get_market_overview(db)
    return ok(data=overview.model_dump()).model_dump()


@router.get(
    "/skills",
    summary="Skill demand rankings and category breakdown",
    response_model=dict,
)
def get_skills_analytics(
    db: DbSession,
    limit: int = Query(20, ge=1, le=100, description="Number of top skills to return"),
    category: SkillCategory | None = Query(None, description="Filter by skill category"),
) -> dict[str, Any]:
    """Retrieve ranking of most in-demand skills and category distribution."""
    data = analytics_service.get_skills_analysis(db, limit=limit, category=category)
    return ok(data=data).model_dump()


@router.get(
    "/roles",
    summary="Role distribution and seniority metrics",
    response_model=dict,
)
def get_roles_analytics(db: DbSession) -> dict[str, Any]:
    """Retrieve job openings share and seniority breakdown across core engineering roles."""
    roles = analytics_service.get_roles_analysis(db)
    return ok(data=roles).model_dump()


@router.get(
    "/salaries",
    summary="Multidimensional salary benchmarks",
    response_model=dict,
)
def get_salaries_analytics(db: DbSession) -> dict[str, Any]:
    """Retrieve salary percentiles segmented by seniority level, role, and remote status."""
    data = analytics_service.get_salary_analysis(db)
    return ok(data=data).model_dump()


@router.get(
    "/geo",
    summary="Geographic distribution and remote work ratios",
    response_model=dict,
)
def get_geo_analytics(
    db: DbSession,
    limit: int = Query(15, ge=1, le=50, description="Top locations to return"),
) -> dict[str, Any]:
    """Retrieve top hiring hubs and remote eligibility metrics."""
    data = analytics_service.get_geo_analysis(db, limit=limit)
    return ok(data=data).model_dump()
