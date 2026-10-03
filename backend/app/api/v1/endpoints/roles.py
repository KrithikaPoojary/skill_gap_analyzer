"""Target role and career path endpoints."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.repositories.role_repo import role_repository
from app.schemas.response import ok
from app.schemas.role import (
    RoleSkillItem,
    TargetRoleDetailRead,
    TargetRoleRead,
    UserTargetRoleCreate,
    UserTargetRoleRead,
)

router = APIRouter(prefix="/roles", tags=["Target Roles & Career Paths"])


@router.get(
    "",
    summary="List active target roles",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def list_target_roles(
    db: DbSession,
    category: str | None = Query(None, description="Filter by career category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Retrieve list of industry target roles available for gap analysis."""
    roles = role_repository.get_active_roles(db, category=category, skip=skip, limit=limit)
    items = [TargetRoleRead.model_validate(r).model_dump() for r in roles]
    return ok(data=items).model_dump()


@router.get(
    "/popular",
    summary="Get most popular target roles tracked by candidates",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_popular_target_roles(
    db: DbSession,
    limit: int = Query(10, ge=1, le=50, description="Max roles to return"),
) -> dict[str, Any]:
    """Retrieve top target roles ranked by number of candidates actively tracking them."""
    popular = role_repository.get_popular_roles(db, limit=limit)
    return ok(data=popular).model_dump()


@router.get(
    "/by-slug/{slug}",
    summary="Get target role by slug",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_role_by_slug(slug: str, db: DbSession) -> dict[str, Any]:
    """Retrieve a target role by its URL-friendly slug."""
    role = role_repository.get_by_slug(db, slug=slug)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target role with slug '{slug}' not found.",
        )
    return ok(data=TargetRoleRead.model_validate(role).model_dump()).model_dump()


@router.get(
    "/{role_id}",
    summary="Get target role details with benchmark skills",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_role_detail(role_id: int, db: DbSession) -> dict[str, Any]:
    """Fetch complete benchmark requirements including weighted core and optional skills."""
    role = role_repository.get_role_with_skills(db, role_id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target role with ID {role_id} not found.",
        )

    skills_data = [
        RoleSkillItem(
            skill_id=rw.skill_id,
            skill_name=rw.skill.name if rw.skill else None,
            weight=rw.weight,
            is_core=rw.is_core,
            benchmark_level=rw.benchmark_level,
        )
        for rw in role.role_skills
    ]
    detail = TargetRoleDetailRead(
        id=role.id,
        title=role.title,
        slug=role.slug,
        description=role.description,
        category=role.category,
        min_experience_years=role.min_experience_years,
        is_active=role.is_active,
        created_at=role.created_at,
        skills=skills_data,
    )
    return ok(data=detail.model_dump()).model_dump()


@router.get(
    "/me/targets",
    summary="List authenticated user's tracked target roles",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_my_target_roles(
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """List career target roles tracked by the authenticated user."""
    assocs = role_repository.get_user_target_roles(db, user_id=current_user.id)
    items = [
        UserTargetRoleRead(
            user_id=a.user_id,
            role_id=a.role_id,
            role_title=a.role.title if a.role else None,
            role_category=a.role.category if a.role else None,
            readiness_score=a.readiness_score,
            target_date=a.target_date,
            created_at=a.created_at,
        ).model_dump()
        for a in assocs
    ]
    return ok(data=items).model_dump()


@router.post(
    "/me/targets",
    summary="Set or update target role tracking for authenticated user",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def set_my_target_role(
    payload: UserTargetRoleCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Track an aspirational target role with optional target achievement date."""
    role = role_repository.get(db, payload.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target role with ID {payload.role_id} not found.",
        )
    assoc = role_repository.assign_user_target_role(
        db,
        user_id=current_user.id,
        role_id=payload.role_id,
        target_date=payload.target_date,
    )
    result = UserTargetRoleRead(
        user_id=assoc.user_id,
        role_id=assoc.role_id,
        role_title=role.title,
        role_category=role.category,
        readiness_score=assoc.readiness_score,
        target_date=assoc.target_date,
        created_at=assoc.created_at,
    )
    return ok(data=result.model_dump(), message="Target role tracked successfully.").model_dump()


@router.delete(
    "/me/targets/{role_id}",
    summary="Untrack a target role for authenticated user",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def remove_my_target_role(
    role_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Remove target role tracking from candidate profile."""
    removed = role_repository.remove_user_target_role(db, user_id=current_user.id, role_id=role_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target role with ID {role_id} is not tracked by user.",
        )
    return ok(data={"role_id": role_id}, message="Target role untracked successfully.").model_dump()
