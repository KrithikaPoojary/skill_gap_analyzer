"""Skill gap analysis REST API endpoints."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.repositories.gap_snapshot_repo import gap_snapshot_repository
from app.schemas.gap_analysis import (
    GapAnalysisSkillsRequest,
    GapAnalysisTextRequest,
    GapSnapshotRead,
)
from app.schemas.response import ok
from app.services.gap_analysis_service import gap_analysis_service

router = APIRouter(prefix="/gap-analysis", tags=["Skill Gap Analysis"])


@router.get(
    "/me",
    summary="Compute skill gap for the authenticated user",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def analyse_my_skill_gap(
    current_user: CurrentUser,
    db: DbSession,
    role_id: int | None = Query(None, description="Target role ID"),
    role_slug: str | None = Query(None, description="Target role slug"),
    role_name: str | None = Query(None, description="Target role title"),
) -> dict[str, Any]:
    """Evaluate current user's claimed skills against a target role and return gap report."""
    if not any([role_id, role_slug, role_name]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify at least one of role_id, role_slug, or role_name.",
        )
    try:
        report = gap_analysis_service.analyse_for_user(
            db,
            user_id=current_user.id,
            role_id=role_id,
            role_name=role_name,
            role_slug=role_slug,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return ok(data=report).model_dump()


@router.post(
    "/analyse",
    summary="Analyse skill gap from an explicit skill list",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def analyse_skill_gap(
    payload: GapAnalysisSkillsRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Calculate matched skills, missing skills, readiness score, and coverage against a target role."""
    report = gap_analysis_service.analyse_skills(
        db,
        profile_skills=payload.skills,
        role_id=payload.role_id,
        role_name=payload.role_name,
        role_slug=payload.role_slug,
    )
    return ok(data=report).model_dump()


@router.post(
    "/analyse-from-text",
    summary="Extract skills from text and compute skill gap",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def analyse_gap_from_text(
    payload: GapAnalysisTextRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Parse unstructured resume or JD text, identify technical competencies, and benchmark against role."""
    result = gap_analysis_service.analyse_from_text(
        db,
        text=payload.text,
        role_id=payload.role_id,
        role_name=payload.role_name,
        role_slug=payload.role_slug,
        min_confidence=payload.min_confidence,
    )
    return ok(data=result).model_dump()


@router.get(
    "/user/{user_id}",
    summary="Compute skill gap for a registered candidate profile",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def analyse_user_skill_gap(
    user_id: int,
    db: DbSession,
    role_id: int | None = Query(None, description="Target role ID"),
    role_slug: str | None = Query(None, description="Target role slug"),
    role_name: str | None = Query(None, description="Target role title"),
) -> dict[str, Any]:
    """Evaluate a registered user's claimed skills against a target role and update readiness score."""
    if not any([role_id, role_slug, role_name]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify at least one of role_id, role_slug, or role_name.",
        )
    try:
        report = gap_analysis_service.analyse_for_user(
            db,
            user_id=user_id,
            role_id=role_id,
            role_name=role_name,
            role_slug=role_slug,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return ok(data=report).model_dump()


@router.get(
    "/me/history",
    summary="List authenticated user's historical skill gap snapshots",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_my_gap_history(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Retrieve chronologically ordered history of candidate readiness evaluations."""
    snapshots = gap_snapshot_repository.list_snapshots(db, user_id=current_user.id, limit=limit)
    items = [GapSnapshotRead.model_validate(s).model_dump() for s in snapshots]
    return ok(data=items).model_dump()


@router.post(
    "/me/snapshot",
    summary="Compute and persist a skill gap snapshot for candidate history",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def save_my_gap_snapshot(
    current_user: CurrentUser,
    db: DbSession,
    role_id: int | None = Query(None, description="Target role ID"),
    role_slug: str | None = Query(None, description="Target role slug"),
    role_name: str | None = Query(None, description="Target role title"),
) -> dict[str, Any]:
    """Calculate current readiness against role and save permanent milestone snapshot."""
    if not any([role_id, role_slug, role_name]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify at least one of role_id, role_slug, or role_name.",
        )
    try:
        report = gap_analysis_service.analyse_for_user(
            db,
            user_id=current_user.id,
            role_id=role_id,
            role_name=role_name,
            role_slug=role_slug,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    matched_formatted = [
        {"name": s} if isinstance(s, str) else s
        for s in report.get("matched_skills", [])
    ]
    snapshot = gap_snapshot_repository.create_snapshot(
        db,
        user_id=current_user.id,
        role_id=report.get("role_id"),
        role_title=report.get("role_name", "Target Role"),
        readiness_score=report.get("coverage_pct", 0.0),
        matched_skills=matched_formatted,
        missing_skills=report.get("missing_skills", []),
    )
    result = GapSnapshotRead.model_validate(snapshot)
    return ok(data=result.model_dump(), message="Skill gap snapshot recorded.").model_dump()


@router.delete(
    "/me/history/{snapshot_id}",
    summary="Delete a historical skill gap snapshot",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def delete_my_gap_snapshot(
    snapshot_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Remove a previously saved skill gap assessment snapshot."""
    removed = gap_snapshot_repository.delete_snapshot(
        db, snapshot_id=snapshot_id, user_id=current_user.id
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot with ID {snapshot_id} not found.",
        )
    return ok(data={"snapshot_id": snapshot_id}, message="Snapshot deleted successfully.").model_dump()

