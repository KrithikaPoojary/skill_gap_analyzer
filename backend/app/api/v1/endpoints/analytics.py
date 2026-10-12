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
    "/summary",
    summary="High-level platform KPI analytics summary",
    response_model=dict,
)
def get_analytics_summary(db: DbSession) -> dict[str, Any]:
    """Retrieve high-level KPI summary (jobs, skills, roles, users, remote ratio)."""
    summary = analytics_service.get_platform_summary(db)
    return ok(data=summary).model_dump()


@router.get(
    "/breakdown",
    summary="Market distribution by employment type and experience level",
    response_model=dict,
)
def get_market_breakdown(db: DbSession) -> dict[str, Any]:
    """Retrieve active job postings breakdown by employment type and seniority level."""
    breakdown = analytics_service.get_market_breakdown(db)
    return ok(data=breakdown).model_dump()



@router.get(
    "/skills/trending",
    summary="Trending and high-importance in-demand skills",
    response_model=dict,
)
def get_trending_skills(
    db: DbSession,
    limit: int = Query(10, ge=1, le=50, description="Number of trending skills to return"),
    min_importance: float = Query(0.0, ge=0.0, le=5.0, description="Minimum skill importance weight"),
) -> dict[str, Any]:
    """Retrieve top trending skills weighted by market penetration and required importance."""
    trending = analytics_service.get_trending_skills(db, limit=limit, min_importance=min_importance)
    return ok(data=trending).model_dump()


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


@router.get(
    "/jobs/by-location",
    summary="Job posting distribution by location",
    response_model=dict,
)
def get_jobs_by_location(
    db: DbSession,
    limit: int = Query(20, ge=1, le=100, description="Max locations to return"),
) -> dict[str, Any]:
    """Return job posting counts grouped by location."""
    from sqlalchemy import select, func
    from app.models.job import JobPosting

    rows = db.execute(
        select(
            JobPosting.location,
            func.count(JobPosting.id).label("count"),
        )
        .where(JobPosting.is_active.is_(True), JobPosting.location.isnot(None))
        .group_by(JobPosting.location)
        .order_by(func.count(JobPosting.id).desc())
        .limit(limit)
    ).all()

    total_with_loc = sum(r.count for r in rows)
    locations = [
        {
            "location": r.location,
            "count": r.count,
            "percentage": round(r.count / total_with_loc * 100, 1) if total_with_loc else 0,
        }
        for r in rows
    ]

    return ok(data={"total_with_location": total_with_loc, "locations": locations}).model_dump()


@router.get(
    "/jobs/by-employment-type",
    summary="Job posting distribution by employment type",
    response_model=dict,
)
def get_jobs_by_employment_type(db: DbSession) -> dict[str, Any]:
    """Return job posting counts grouped by employment type (full_time, contract, etc.)."""
    from sqlalchemy import select, func
    from app.models.job import JobPosting

    rows = db.execute(
        select(
            JobPosting.employment_type,
            func.count(JobPosting.id).label("count"),
        )
        .where(JobPosting.is_active.is_(True))
        .group_by(JobPosting.employment_type)
        .order_by(func.count(JobPosting.id).desc())
    ).all()

    total = sum(r.count for r in rows)
    types = [
        {
            "employment_type": r.employment_type,
            "count": r.count,
            "percentage": round(r.count / total * 100, 1) if total else 0,
        }
        for r in rows
    ]

    return ok(data={"total": total, "types": types}).model_dump()
