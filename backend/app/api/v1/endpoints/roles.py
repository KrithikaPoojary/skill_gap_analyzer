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
    q: str | None = Query(None, description="Search term to filter roles by title or description"),
    category: str | None = Query(None, description="Filter by career category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> dict[str, Any]:
    """Retrieve list of industry target roles available for gap analysis."""
    roles = role_repository.get_active_roles(db, category=category, query=q, skip=skip, limit=limit)
    items = [TargetRoleRead.model_validate(r).model_dump() for r in roles]
    return ok(data=items).model_dump()


@router.get(
    "/categories",
    summary="List target role categories with role counts",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_role_categories(db: DbSession) -> dict[str, Any]:
    """Retrieve all available career role categories with active role counts."""
    categories = role_repository.get_categories(db)
    return ok(data=categories).model_dump()


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
    "/by-experience",
    summary="Filter active target roles by required experience range",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_roles_by_experience(
    db: DbSession,
    min_exp: int | None = Query(None, ge=0, description="Minimum years of experience required"),
    max_exp: int | None = Query(None, ge=0, description="Maximum years of experience required"),
    category: str | None = Query(None, description="Optional career category filter"),
    limit: int = Query(20, ge=1, le=100, description="Max roles to return"),
) -> dict[str, Any]:
    """Retrieve active target roles filtered by the experience range the candidate has."""
    from sqlalchemy import select
    from app.models.role import TargetRole

    stmt = select(TargetRole).where(TargetRole.is_active.is_(True))
    if min_exp is not None:
        stmt = stmt.where(TargetRole.min_experience_years >= min_exp)
    if max_exp is not None:
        stmt = stmt.where(TargetRole.min_experience_years <= max_exp)
    if category:
        stmt = stmt.where(TargetRole.category == category)
    stmt = stmt.order_by(TargetRole.min_experience_years.asc()).limit(limit)

    roles = list(db.scalars(stmt).all())
    items = [TargetRoleRead.model_validate(r).model_dump() for r in roles]
    return ok(data={"total": len(items), "roles": items}).model_dump()


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
    "/{role_id}/skills",
    summary="Get required skills for a target role",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_role_skills(role_id: int, db: DbSession) -> dict[str, Any]:
    """Retrieve benchmark skills, weights, and proficiency requirements for a role."""
    role = role_repository.get_role_with_skills(db, role_id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target role with ID {role_id} not found.",
        )
    skills_data = [
        {
            "skill_id": rw.skill_id,
            "skill_name": rw.skill.name if rw.skill else None,
            "category": rw.skill.category if rw.skill else None,
            "weight": rw.weight,
            "is_core": rw.is_core,
            "benchmark_level": rw.benchmark_level,
        }
        for rw in sorted(role.role_skills, key=lambda x: (x.is_core, x.weight), reverse=True)
    ]
    return ok(
        data={
            "role_id": role.id,
            "title": role.title,
            "total_skills": len(skills_data),
            "skills": skills_data,
        }
    ).model_dump()


@router.get(
    "/{role_id}/similar",
    summary="Get similar target roles in the same category",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_similar_roles(
    role_id: int,
    db: DbSession,
    limit: int = Query(5, ge=1, le=20, description="Max similar roles to return"),
) -> dict[str, Any]:
    """Retrieve other active roles within the same career category."""
    role = role_repository.get(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target role with ID {role_id} not found.",
        )
    similar = role_repository.get_similar_roles(db, role_id=role_id, limit=limit)
    items = [TargetRoleRead.model_validate(r).model_dump() for r in similar]
    return ok(
        data={
            "role_id": role.id,
            "role_title": role.title,
            "category": role.category,
            "similar_roles": items,
        }
    ).model_dump()


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


@router.get(
    "/me/targets/{role_id}",
    summary="Check if a target role is tracked and get readiness score",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_my_target_role_status(
    role_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Check if the authenticated user is tracking this target role."""
    assoc = role_repository.get_user_target_role(db, user_id=current_user.id, role_id=role_id)
    if not assoc:
        return ok(data={"is_tracked": False, "role_id": role_id, "tracking": None}).model_dump()
    data = {
        "is_tracked": True,
        "role_id": assoc.role_id,
        "role_title": assoc.role.title if assoc.role else None,
        "readiness_score": assoc.readiness_score,
        "target_date": assoc.target_date.isoformat() if assoc.target_date else None,
        "created_at": assoc.created_at.isoformat() if assoc.created_at else None,
    }
    return ok(data={"is_tracked": True, "role_id": role_id, "tracking": data}).model_dump()


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


@router.get(
    "/{role_id}/overlap/{target_role_id}",
    summary="Compare skill requirements and overlap between two target roles",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_role_skill_overlap(
    role_id: int,
    target_role_id: int,
    db: DbSession,
) -> dict[str, Any]:
    """Calculate shared vs distinct skills between two roles with similarity percentage."""
    role1 = role_repository.get_role_with_skills(db, role_id=role_id)
    if not role1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source target role with ID {role_id} not found.",
        )

    role2 = role_repository.get_role_with_skills(db, role_id=target_role_id)
    if not role2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison target role with ID {target_role_id} not found.",
        )

    s1_map = {rw.skill_id: rw for rw in role1.role_skills}
    s2_map = {rw.skill_id: rw for rw in role2.role_skills}

    s1_keys = set(s1_map.keys())
    s2_keys = set(s2_map.keys())

    shared_keys = s1_keys & s2_keys
    only_s1_keys = s1_keys - s2_keys
    only_s2_keys = s2_keys - s1_keys
    union_keys = s1_keys | s2_keys

    overlap_pct = round(len(shared_keys) / len(union_keys) * 100, 1) if union_keys else 0.0

    shared_skills = [
        {
            "skill_id": sid,
            "skill_name": s1_map[sid].skill.name if s1_map[sid].skill else None,
            "category": s1_map[sid].skill.category if s1_map[sid].skill else None,
            "role1_is_core": s1_map[sid].is_core,
            "role2_is_core": s2_map[sid].is_core,
            "role1_weight": s1_map[sid].weight,
            "role2_weight": s2_map[sid].weight,
        }
        for sid in sorted(shared_keys)
    ]

    role1_unique = [
        {
            "skill_id": sid,
            "skill_name": s1_map[sid].skill.name if s1_map[sid].skill else None,
            "category": s1_map[sid].skill.category if s1_map[sid].skill else None,
            "is_core": s1_map[sid].is_core,
            "weight": s1_map[sid].weight,
        }
        for sid in sorted(only_s1_keys)
    ]

    role2_unique = [
        {
            "skill_id": sid,
            "skill_name": s2_map[sid].skill.name if s2_map[sid].skill else None,
            "category": s2_map[sid].skill.category if s2_map[sid].skill else None,
            "is_core": s2_map[sid].is_core,
            "weight": s2_map[sid].weight,
        }
        for sid in sorted(only_s2_keys)
    ]

    return ok(
        data={
            "role1": {"id": role1.id, "title": role1.title, "total_skills": len(s1_keys)},
            "role2": {"id": role2.id, "title": role2.title, "total_skills": len(s2_keys)},
            "overlap_percentage": overlap_pct,
            "shared_count": len(shared_keys),
            "role1_unique_count": len(only_s1_keys),
            "role2_unique_count": len(only_s2_keys),
            "shared_skills": shared_skills,
            "role1_unique_skills": role1_unique,
            "role2_unique_skills": role2_unique,
        }
    ).model_dump()


@router.get(
    "/{role_id}/transitions",
    summary="Career transition recommendations based on skill transferability",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_role_transitions(
    role_id: int,
    db: DbSession,
    limit: int = Query(5, ge=1, le=20, description="Max transition paths to recommend"),
) -> dict[str, Any]:
    """Identify target roles with high skill transferability from the given role."""
    from app.models.role import TargetRole

    source_role = role_repository.get_role_with_skills(db, role_id=role_id)
    if not source_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target role with ID {role_id} not found.",
        )

    source_skill_ids = {rw.skill_id for rw in source_role.role_skills}
    other_roles = db.query(TargetRole).filter(TargetRole.id != role_id, TargetRole.is_active.is_(True)).all()

    recommendations = []
    for other in other_roles:
        other_detail = role_repository.get_role_with_skills(db, role_id=other.id)
        if not other_detail or not other_detail.role_skills:
            continue
        other_skill_ids = {rw.skill_id for rw in other_detail.role_skills}
        shared = source_skill_ids & other_skill_ids
        if not shared:
            continue
        transferability_pct = round(len(shared) / len(other_skill_ids) * 100, 1)
        recommendations.append(
            {
                "role_id": other.id,
                "title": other.title,
                "category": other.category,
                "min_experience_years": other.min_experience_years,
                "shared_skills_count": len(shared),
                "total_target_skills": len(other_skill_ids),
                "transferability_pct": transferability_pct,
            }
        )

    recommendations.sort(key=lambda x: (x["transferability_pct"], x["shared_skills_count"]), reverse=True)
    recommendations = recommendations[:limit]

    return ok(
        data={
            "source_role": {"id": source_role.id, "title": source_role.title, "total_skills": len(source_skill_ids)},
            "total_recommendations": len(recommendations),
            "transitions": recommendations,
        }
    ).model_dump()


