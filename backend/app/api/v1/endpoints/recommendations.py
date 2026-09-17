"""Career role recommendations REST API endpoints."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DbSession
from app.schemas.recommendations import (
    RecommendationsForSkillsRequest,
    RecommendationsForTextRequest,
    RecommendationsResponse,
    RoleRecommendationItem,
    TextRecommendationsResponse,
)
from app.schemas.response import ok
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["Role Recommendations"])


@router.get(
    "/user/{user_id}",
    summary="Get personalized career role recommendations for a registered user",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_user_recommendations(
    user_id: int,
    db: DbSession,
    limit: int = Query(5, ge=1, le=50, description="Max recommendations to return"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum fit score filter"),
    category: str | None = Query(None, description="Role category filter"),
) -> dict[str, Any]:
    """Rank target career roles for a registered user based on their claimed skill profile."""
    try:
        recs = recommendation_service.recommend_for_user(
            db,
            user_id=user_id,
            limit=limit,
            min_score=min_score,
            category=category,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    response_data = RecommendationsResponse(
        recommendations=[RoleRecommendationItem(**r) for r in recs]
    )
    return ok(data=response_data.model_dump()).model_dump()


@router.post(
    "/from-skills",
    summary="Generate role recommendations from an explicit list of skills",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_recommendations_from_skills(
    payload: RecommendationsForSkillsRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Compute and rank top career role matches for an ad-hoc list of skills."""
    recs = recommendation_service.recommend_for_skills(
        db,
        skills=payload.skills,
        limit=payload.limit,
        min_score=payload.min_score,
        category=payload.category,
    )

    response_data = RecommendationsResponse(
        recommendations=[RoleRecommendationItem(**r) for r in recs]
    )
    return ok(data=response_data.model_dump()).model_dump()


@router.post(
    "/from-text",
    summary="Extract skills from text and generate role recommendations",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_recommendations_from_text(
    payload: RecommendationsForTextRequest,
    db: DbSession,
) -> dict[str, Any]:
    """Extract skills from free-form resume or profile text and deliver ranked role recommendations."""
    result = recommendation_service.recommend_for_text(
        db,
        text=payload.text,
        limit=payload.limit,
        min_score=payload.min_score,
        category=payload.category,
        min_confidence=payload.min_confidence,
    )

    response_data = TextRecommendationsResponse(
        extracted_skills=result["extracted_skills"],
        recommendations=[RoleRecommendationItem(**r) for r in result["recommendations"]],
    )
    return ok(data=response_data.model_dump()).model_dump()
