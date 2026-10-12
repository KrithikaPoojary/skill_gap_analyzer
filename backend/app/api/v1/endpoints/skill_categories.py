"""Skill category distribution and summary endpoints.

Provides category-level aggregations showing how skills are distributed
across the taxonomy (language, framework, database, cloud_devops, etc.).
"""

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import DbSession
from app.models.skill import Skill, SkillCategory
from app.schemas.response import ok

router = APIRouter(prefix="/skills", tags=["Skill Extraction"])


@router.get(
    "/categories/summary",
    summary="Get skill count breakdown by category",
    response_model=dict,
)
def get_skill_category_summary(db: DbSession) -> dict[str, Any]:
    """Return the number of skills in each taxonomy category."""
    rows = db.execute(
        select(Skill.category, func.count(Skill.id).label("count"))
        .group_by(Skill.category)
        .order_by(func.count(Skill.id).desc())
    ).all()

    categories = [{"category": row.category, "count": row.count} for row in rows]
    total = sum(c["count"] for c in categories)

    return ok(
        data={
            "total_skills": total,
            "categories": categories,
        }
    ).model_dump()


@router.get(
    "/categories/{category}/skills",
    summary="List all skills in a specific category",
    response_model=dict,
)
def get_skills_by_category(
    category: str,
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Return paginated skills filtered by the given category slug."""
    query = (
        select(Skill)
        .where(Skill.category == category)
        .order_by(Skill.name)
        .offset(offset)
        .limit(limit)
    )
    skills = db.scalars(query).all()
    total = db.scalar(
        select(func.count(Skill.id)).where(Skill.category == category)
    ) or 0

    items = [
        {
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "is_verified": s.is_verified,
        }
        for s in skills
    ]

    return ok(
        data={
            "category": category,
            "total": total,
            "limit": limit,
            "offset": offset,
            "skills": items,
        }
    ).model_dump()
