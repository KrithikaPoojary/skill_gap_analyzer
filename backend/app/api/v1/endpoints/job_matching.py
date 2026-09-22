"""Job matching REST API endpoints."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.associations import UserSkill
from app.models.user import Profile
from app.schemas.job_match import (
    JobMatchCriteria,
    JobMatchScoreDetail,
    PaginatedJobMatchResponse,
)
from app.schemas.response import ok
from app.services.job_match_service import job_match_service
from sqlalchemy import select
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/jobs", tags=["Job Matching & Applications"])


@router.post(
    "/match",
    summary="Match and rank jobs against explicit candidate criteria",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def match_jobs(
    criteria: JobMatchCriteria,
    db: DbSession,
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Page size limit"),
) -> dict[str, Any]:
    """Calculate multi-factor match scores and return ranked jobs."""
    results = job_match_service.match_jobs(db, criteria, offset=offset, limit=limit)
    return ok(data=results.model_dump()).model_dump()


@router.get(
    "/match/me",
    summary="Get personalized job matches for the authenticated user",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def match_jobs_for_me(
    current_user: CurrentUser,
    db: DbSession,
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Page size limit"),
    min_match_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum match score"),
) -> dict[str, Any]:
    """Evaluate current user's profile and claimed skills against all active job postings."""
    try:
        results = job_match_service.match_for_user(
            db,
            user_id=current_user.id,
            offset=offset,
            limit=limit,
            min_match_score=min_match_score,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return ok(data=results.model_dump()).model_dump()


@router.get(
    "/{job_id}/match-score",
    summary="Compute match score between authenticated user and a specific job",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_job_match_score(
    job_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Calculate detailed multi-factor breakdown for a specific job posting."""
    # Pull current user skills
    stmt = select(UserSkill).where(UserSkill.user_id == current_user.id).options(joinedload(UserSkill.skill))
    skills = [s.skill.name for s in db.scalars(stmt).unique().all() if s.skill and s.skill.name]
    profile = db.scalar(select(Profile).where(Profile.user_id == current_user.id))

    detail = job_match_service.match_single_job(
        db,
        job_id=job_id,
        candidate_skills=skills if skills else ["Software Engineering"],
        candidate_years=profile.years_of_experience if profile else None,
        candidate_location=profile.location if profile else None,
    )
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job posting with ID {job_id} not found.",
        )

    return ok(data=detail.model_dump()).model_dump()
