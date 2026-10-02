"""Job matching REST API endpoints."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.associations import UserSkill
from app.models.saved_job import ApplicationStatus
from app.models.user import Profile
from app.repositories.saved_job_repo import saved_job_repository
from app.schemas.job_match import (
    JobApplicationStatusUpdateRequest,
    JobMatchCriteria,
    JobMatchScoreDetail,
    JobSaveRequest,
    PaginatedJobMatchResponse,
    PaginatedSavedJobResponse,
    SavedJobRead,
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


@router.post(
    "/{job_id}/save",
    summary="Bookmark a job posting for the authenticated user",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def save_job(
    job_id: int,
    current_user: CurrentUser,
    db: DbSession,
    payload: JobSaveRequest | None = None,
) -> dict[str, Any]:
    """Bookmark a job posting and optionally record personal notes."""
    notes = payload.notes if payload else None
    saved = saved_job_repository.save_job(db, user_id=current_user.id, job_id=job_id, notes=notes)
    read_obj = SavedJobRead(
        id=saved.id,
        user_id=saved.user_id,
        job_id=saved.job_id,
        status=saved.status.value,
        notes=saved.notes,
        applied_at=saved.applied_at,
        created_at=saved.created_at,
        updated_at=saved.updated_at,
        job_title=saved.job.title if saved.job else None,
        company_name=saved.job.company_name if saved.job else None,
        location=saved.job.location if saved.job else None,
        is_remote=saved.job.is_remote if saved.job else None,
    )
    return ok(data=read_obj.model_dump(), message="Job bookmarked successfully.").model_dump()


@router.delete(
    "/{job_id}/save",
    summary="Remove a bookmarked job for the authenticated user",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def remove_saved_job(
    job_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Remove a job from user's bookmarks."""
    removed = saved_job_repository.remove_saved_job(db, user_id=current_user.id, job_id=job_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bookmarked job with ID {job_id} not found.",
        )
    return ok(data={"removed": True}, message="Job removed from bookmarks.").model_dump()


@router.get(
    "/saved",
    summary="List all bookmarked and tracked jobs for the authenticated user",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def list_saved_jobs(
    current_user: CurrentUser,
    db: DbSession,
    status_filter: str | None = Query(None, alias="status", description="Filter by status (saved, applied, etc.)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Page size limit"),
) -> dict[str, Any]:
    """Retrieve bookmarked jobs and recruitment pipeline progress."""
    app_status = None
    if status_filter:
        try:
            app_status = ApplicationStatus(status_filter.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{status_filter}'. Valid statuses: {[s.value for s in ApplicationStatus]}",
            )

    records = saved_job_repository.list_by_user(
        db, user_id=current_user.id, status=app_status, offset=offset, limit=limit
    )
    total = saved_job_repository.count_by_user(db, user_id=current_user.id, status=app_status)

    items = [
        SavedJobRead(
            id=r.id,
            user_id=r.user_id,
            job_id=r.job_id,
            status=r.status.value,
            notes=r.notes,
            applied_at=r.applied_at,
            created_at=r.created_at,
            updated_at=r.updated_at,
            job_title=r.job.title if r.job else None,
            company_name=r.job.company_name if r.job else None,
            location=r.job.location if r.job else None,
            is_remote=r.job.is_remote if r.job else None,
        )
        for r in records
    ]

    response_payload = PaginatedSavedJobResponse(
        items=items, total=total, offset=offset, limit=limit
    )
    return ok(data=response_payload.model_dump()).model_dump()


@router.patch(
    "/{job_id}/status",
    summary="Update application tracking status for a bookmarked job",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def update_application_status(
    job_id: int,
    payload: JobApplicationStatusUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Update lifecycle status (e.g. applied, interviewing, offered, rejected)."""
    try:
        app_status = ApplicationStatus(payload.status.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Valid statuses: {[s.value for s in ApplicationStatus]}",
        )

    updated = saved_job_repository.update_status(
        db,
        user_id=current_user.id,
        job_id=job_id,
        status=app_status,
        notes=payload.notes,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bookmarked job with ID {job_id} not found.",
        )

    read_obj = SavedJobRead(
        id=updated.id,
        user_id=updated.user_id,
        job_id=updated.job_id,
        status=updated.status.value,
        notes=updated.notes,
        applied_at=updated.applied_at,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
        job_title=updated.job.title if updated.job else None,
        company_name=updated.job.company_name if updated.job else None,
        location=updated.job.location if updated.job else None,
        is_remote=updated.job.is_remote if updated.job else None,
    )
    return ok(data=read_obj.model_dump(), message="Application status updated.").model_dump()
