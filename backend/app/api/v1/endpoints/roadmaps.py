"""Learning Roadmap REST API endpoints."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.schemas.response import ok
from app.schemas.roadmap import (
    MilestoneProgressUpdateRequest,
    RoadmapGenerateFromTextRequest,
    RoadmapGenerateRequest,
    RoadmapResponse,
)
from app.services.roadmap_service import roadmap_service

router = APIRouter(prefix="/roadmaps", tags=["Learning Roadmaps"])


@router.post(
    "/generate",
    summary="Generate transient learning roadmap from missing skills",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def generate_roadmap(payload: RoadmapGenerateRequest) -> dict[str, Any]:
    """Calculate DAG dependency sequence, multi-phase milestones, and study timeline."""
    roadmap_data = roadmap_service.generate_transient(
        missing_skills=payload.missing_skills,
        role_title=payload.role_title,
        weekly_commitment_hours=payload.weekly_commitment_hours,
    )
    return ok(data=roadmap_data).model_dump()


@router.post(
    "/generate-from-text",
    summary="Extract skills from text, compute gap against role, and generate roadmap",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def generate_roadmap_from_text(
    payload: RoadmapGenerateFromTextRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Parse unstructured resume text, identify missing skills, and build prioritized learning path."""
    result = roadmap_service.generate_from_text(
        db,
        text=payload.text,
        role_name=payload.role_name,
        role_slug=payload.role_slug,
        weekly_commitment_hours=payload.weekly_commitment_hours,
        min_confidence=payload.min_confidence,
    )
    return ok(data=result).model_dump()


@router.post(
    "/user/{user_id}",
    summary="Generate and persist learning roadmap for a registered user",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def create_user_roadmap(
    user_id: int,
    db: DbSession,
    role_id: int | None = Query(None, description="Target role ID"),
    role_name: str | None = Query(None, description="Target role title"),
    role_slug: str | None = Query(None, description="Target role slug"),
    weekly_commitment_hours: int = Query(10, ge=1, le=80, description="Weekly study hours"),
) -> dict[str, Any]:
    """Evaluate candidate profile deficits, sequence multi-phase curriculum, and save to database."""
    if not any([role_id, role_name, role_slug]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify at least one of role_id, role_name, or role_slug.",
        )
    try:
        saved = roadmap_service.create_and_persist_for_user(
            db,
            user_id=user_id,
            role_id=role_id,
            role_name=role_name,
            role_slug=role_slug,
            weekly_commitment_hours=weekly_commitment_hours,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return ok(data=saved, message="Roadmap created and persisted successfully.").model_dump()


@router.get(
    "/user/{user_id}",
    summary="Get saved learning roadmaps for a user",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def list_user_roadmaps(
    user_id: int,
    db: DbSession,
    status_filter: str | None = Query(None, alias="status", description="Filter by active/completed"),
) -> dict[str, Any]:
    """Retrieve all roadmaps associated with a candidate profile."""
    roadmaps = roadmap_service.get_user_roadmaps(db, user_id=user_id, status=status_filter)
    return ok(data={"roadmaps": roadmaps, "total": len(roadmaps)}).model_dump()


@router.get(
    "/{roadmap_id}",
    summary="Get roadmap details by ID",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_roadmap_details(roadmap_id: int, db: DbSession) -> dict[str, Any]:
    """Fetch complete learning roadmap with milestones, skills, and resources."""
    roadmap = roadmap_service.get_roadmap_by_id(db, roadmap_id=roadmap_id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Roadmap with ID {roadmap_id} not found.",
        )
    return ok(data=roadmap).model_dump()


@router.patch(
    "/{roadmap_id}/milestones/{milestone_id}",
    summary="Update milestone completion progress",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def update_milestone_progress(
    roadmap_id: int,
    milestone_id: int,
    payload: MilestoneProgressUpdateRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Mark a roadmap milestone as completed or pending."""
    updated = roadmap_service.update_milestone_progress(
        db, milestone_id=milestone_id, is_completed=payload.is_completed
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Milestone with ID {milestone_id} not found.",
        )
    return ok(data=updated, message="Milestone progress updated.").model_dump()
