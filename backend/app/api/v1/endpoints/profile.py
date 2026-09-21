"""User profile and candidate skills REST API endpoints."""

from typing import Any
from fastapi import APIRouter, Body, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.profile import (
    FullProfileResponse,
    ProfileData,
    ProfileUpsertRequest,
    UserSkillCreateRequest,
    UserSkillResponse,
)
from app.schemas.response import ok
from app.services.profile_service import profile_service
from app.services.user_skill_service import user_skill_service

router = APIRouter(prefix="/profile", tags=["User Profile"])


@router.get(
    "/me",
    summary="Get authenticated candidate profile",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_my_profile(current_user: CurrentUser, db: DbSession) -> dict[str, Any]:
    """Retrieve full profile for the currently logged-in user."""
    profile_data = profile_service.get_full_profile(db, user_id=current_user.id)
    if not profile_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for current user.",
        )
    return ok(data=profile_data).model_dump()


@router.put(
    "/me",
    summary="Update authenticated candidate profile",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def update_my_profile(
    payload: ProfileUpsertRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Update profile metadata for the currently logged-in user."""
    try:
        profile = profile_service.upsert_profile(
            db,
            user_id=current_user.id,
            **payload.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    profile_dict = ProfileData.model_validate(profile).model_dump()
    return ok(data=profile_dict, message="Profile updated successfully.").model_dump()


@router.post(
    "/me/skills",
    summary="Add or update a skill on authenticated profile",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def add_my_skill(
    payload: UserSkillCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Associate a technical skill with current candidate profile."""
    try:
        user_skill = user_skill_service.add_user_skill(
            db,
            user_id=current_user.id,
            skill_id=payload.skill_id,
            skill_name=payload.skill_name,
            proficiency_level=payload.proficiency_level,
            years_of_experience=payload.years_of_experience,
            is_verified=payload.is_verified,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    skill_data = {
        "skill_id": user_skill.skill_id,
        "name": user_skill.skill.name if user_skill.skill else None,
        "normalized_name": user_skill.skill.normalized_name if user_skill.skill else None,
        "category": user_skill.skill.category if user_skill.skill else None,
        "proficiency_level": user_skill.proficiency_level,
        "years_of_experience": user_skill.years_of_experience,
        "is_verified": user_skill.is_verified,
    }
    return ok(data=skill_data, message="Skill added to your profile.").model_dump()


@router.post(
    "/me/skills/bulk",
    summary="Bulk add skills to authenticated profile",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def bulk_add_my_skills(
    current_user: CurrentUser,
    skills: list[str] = Body(..., embed=True, description="List of skill names to associate"),
    proficiency_level: str = Body("intermediate", embed=True),
    db: DbSession = None,
) -> dict[str, Any]:
    """Bulk associate skill names with current candidate profile."""
    try:
        added = user_skill_service.bulk_add_user_skills(
            db,
            user_id=current_user.id,
            skill_names=skills,
            proficiency_level=proficiency_level,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ok(
        data={"added_count": len(added), "skills": [us.skill.name for us in added if us.skill]},
        message=f"Added {len(added)} skills to your profile.",
    ).model_dump()


@router.delete(
    "/me/skills/{skill_id}",
    summary="Remove a skill from authenticated profile",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def remove_my_skill(
    skill_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """Detach a skill from current candidate profile."""
    removed = user_skill_service.remove_user_skill(db, user_id=current_user.id, skill_id=skill_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found on your profile.",
        )
    return ok(data={"removed": True}, message="Skill removed from your profile.").model_dump()


@router.get(
    "/{user_id}",
    summary="Get aggregated user profile",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_user_profile(user_id: int, db: DbSession) -> dict[str, Any]:
    """Retrieve complete candidate profile including claimed skills and target career roles."""
    profile_data = profile_service.get_full_profile(db, user_id=user_id)
    if not profile_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )
    return ok(data=profile_data).model_dump()


@router.put(
    "/{user_id}",
    summary="Create or update candidate profile",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def upsert_user_profile(
    user_id: int,
    payload: ProfileUpsertRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Create or modify professional profile metadata for the specified user."""
    try:
        profile = profile_service.upsert_profile(
            db,
            user_id=user_id,
            **payload.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    profile_dict = ProfileData.model_validate(profile).model_dump()
    return ok(data=profile_dict, message="Profile updated successfully.").model_dump()


@router.post(
    "/{user_id}/skills",
    summary="Add or update a skill on user profile",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def add_user_skill(
    user_id: int,
    payload: UserSkillCreateRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Associate a technical skill with candidate profile, specifying proficiency and experience."""
    try:
        user_skill = user_skill_service.add_user_skill(
            db,
            user_id=user_id,
            skill_id=payload.skill_id,
            skill_name=payload.skill_name,
            proficiency_level=payload.proficiency_level,
            years_of_experience=payload.years_of_experience,
            is_verified=payload.is_verified,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    skill_data = {
        "skill_id": user_skill.skill_id,
        "name": user_skill.skill.name if user_skill.skill else None,
        "normalized_name": user_skill.skill.normalized_name if user_skill.skill else None,
        "category": user_skill.skill.category if user_skill.skill else None,
        "proficiency_level": user_skill.proficiency_level,
        "years_of_experience": user_skill.years_of_experience,
        "is_verified": user_skill.is_verified,
    }
    return ok(data=skill_data, message="Skill added to profile.").model_dump()


@router.post(
    "/{user_id}/skills/bulk",
    summary="Bulk add skills to user profile",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def bulk_add_user_skills(
    user_id: int,
    skills: list[str] = Body(..., embed=True, description="List of skill names to associate"),
    proficiency_level: str = Body("intermediate", embed=True),
    db: DbSession = None,
) -> dict[str, Any]:
    """Bulk associate a list of skill names with candidate profile (e.g. from resume extraction)."""
    try:
        added = user_skill_service.bulk_add_user_skills(
            db,
            user_id=user_id,
            skill_names=skills,
            proficiency_level=proficiency_level,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ok(
        data={"added_count": len(added), "skills": [us.skill.name for us in added if us.skill]},
        message=f"Added {len(added)} skills to profile.",
    ).model_dump()


@router.delete(
    "/{user_id}/skills/{skill_id}",
    summary="Remove a skill from user profile",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def remove_user_skill(
    user_id: int,
    skill_id: int,
    db: DbSession,
) -> dict[str, Any]:
    """Detach a skill from candidate profile."""
    removed = user_skill_service.remove_user_skill(db, user_id=user_id, skill_id=skill_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill {skill_id} not found on profile {user_id}.",
        )
    return ok(data={"removed": True}, message="Skill removed from profile.").model_dump()
