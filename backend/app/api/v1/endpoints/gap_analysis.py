"""Skill gap analysis REST API endpoints."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.repositories.gap_snapshot_repo import gap_snapshot_repository
from app.schemas.gap_analysis import (
    CompareRolesRequest,
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


@router.get(
    "/me/history/stats",
    summary="Get aggregated statistics and readiness trend across user snapshots",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_my_gap_history_stats(
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Calculate summary statistics over candidate gap analysis history including trend."""
    stats = gap_snapshot_repository.get_user_snapshot_stats(db, user_id=current_user.id)
    return ok(data=stats).model_dump()


@router.get(
    "/me/snapshot/latest",
    summary="Get the most recent skill gap snapshot for the authenticated user",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_my_latest_snapshot(
    current_user: CurrentUser,
    db: DbSession,
    role_id: int | None = Query(None, description="Filter latest snapshot by role ID"),
) -> dict[str, Any]:
    """Retrieve the most recent skill gap assessment snapshot for the current user."""
    snapshot = gap_snapshot_repository.get_latest_snapshot(
        db, user_id=current_user.id, role_id=role_id
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No gap analysis snapshot found for this user.",
        )
    return ok(data=GapSnapshotRead.model_validate(snapshot).model_dump()).model_dump()


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


@router.post(
    "/compare",
    summary="Compare skill gap across multiple target roles side-by-side",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def compare_roles(
    payload: CompareRolesRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Evaluate candidate skills against multiple target roles to determine best fit."""
    skills = payload.skills or []
    result = gap_analysis_service.compare_roles(db, skills=skills, role_queries=payload.roles)
    return ok(data=result).model_dump()


@router.post(
    "/me/compare",
    summary="Compare authenticated user's profile against multiple roles",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def compare_my_roles(
    payload: CompareRolesRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Evaluate current user's profile against multiple target roles side-by-side."""
    result = gap_analysis_service.compare_roles_for_user(
        db, user_id=current_user.id, role_queries=payload.roles
    )
    return ok(data=result).model_dump()


@router.get(
    "/me/readiness",
    summary="Get readiness scores across all active target roles for the authenticated user",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_my_readiness_dashboard(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(10, ge=1, le=50, description="Max roles to evaluate"),
) -> dict[str, Any]:
    """Evaluate authenticated user's skill profile against all active target roles and rank by readiness."""
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload
    from app.models.role import RoleSkillWeighting, TargetRole
    from app.services.skill_gap_analyzer import SkillWeight
    from app.services.user_skill_service import user_skill_service

    claimed_skills = user_skill_service.get_user_skill_names(db, user_id=current_user.id)

    stmt = (
        select(TargetRole)
        .where(TargetRole.is_active.is_(True))
        .options(joinedload(TargetRole.role_skills).joinedload(RoleSkillWeighting.skill))
    )
    roles = list(db.scalars(stmt).unique().all())

    readiness_entries = []
    for role in roles:
        required_weights = [
            SkillWeight(name=rw.skill.name, weight=rw.weight)
            for rw in role.role_skills
            if rw.skill
        ]
        if not required_weights:
            continue
        report = gap_analysis_service.analyzer.analyse(
            profile_skills=claimed_skills,
            required_skills=required_weights,
            role_name=role.title,
        )
        readiness_entries.append({
            "role_id": role.id,
            "title": role.title,
            "slug": role.slug,
            "category": role.category,
            "readiness_score": round(report.coverage_pct, 2),
            "match_score": round(report.weighted_gap_score, 3),
            "missing_count": len(report.missing_skills),
            "missing_critical": report.missing_critical,
        })

    readiness_entries.sort(key=lambda r: r["readiness_score"], reverse=True)
    top = readiness_entries[:limit]

    return ok(
        data={
            "user_id": current_user.id,
            "total_roles_evaluated": len(readiness_entries),
            "roles": top,
        }
    ).model_dump()


@router.get(
    "/benchmark/{role_id}",
    summary="Benchmark candidate readiness against peer cohort for a target role",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_role_peer_benchmark(
    role_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Compare candidate's readiness score against other candidates tracking the same target role."""
    from sqlalchemy import select
    from app.models.role import TargetRole, UserTargetRole

    role = db.get(TargetRole, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target role with ID {role_id} not found.",
        )

    try:
        report = gap_analysis_service.analyse_for_user(
            db, user_id=current_user.id, role_id=role_id
        )
        candidate_score = report.get("coverage_pct", 0.0)
    except Exception:
        candidate_score = 0.0

    stmt = select(UserTargetRole.readiness_score).where(UserTargetRole.role_id == role_id)
    cohort_scores = list(db.scalars(stmt).all())

    cohort_size = len(cohort_scores)
    if cohort_size > 0:
        avg_score = round(sum(cohort_scores) / cohort_size, 2)
        max_score = round(max(cohort_scores), 2)
        below_count = sum(1 for s in cohort_scores if s <= candidate_score)
        percentile = round((below_count / cohort_size) * 100, 1)
    else:
        avg_score = candidate_score
        max_score = candidate_score
        percentile = 100.0

    return ok(
        data={
            "role_id": role.id,
            "role_title": role.title,
            "candidate_readiness_score": candidate_score,
            "cohort_size": cohort_size,
            "average_readiness_score": avg_score,
            "max_readiness_score": max_score,
            "percentile_rank": percentile,
            "is_above_average": candidate_score >= avg_score,
        }
    ).model_dump()

