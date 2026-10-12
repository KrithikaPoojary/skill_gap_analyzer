"""Skill extraction NLP and text analysis REST API endpoints."""

import time
from typing import Any

from fastapi import APIRouter, Query, status

from app.api.deps import DbSession
from app.repositories.skill_repo import skill_repository
from app.schemas.extraction import (
    BatchExtractionRequest,
    BatchExtractionResponse,
    BatchExtractionResultItem,
    SkillExtractionItemSchema,
    SkillExtractionRequest,
    SkillExtractionResponse,
)
from app.schemas.response import ok
from app.services.extractor.batch_extractor import batch_skill_extractor
from app.services.skill_extractor import skill_extractor

router = APIRouter(prefix="/skills", tags=["Skill Extraction"])


@router.get(
    "/categories",
    summary="List skill taxonomy categories and counts",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def list_skill_categories(db: DbSession) -> dict[str, Any]:
    """Retrieve all available skill categories with current skill counts."""
    stats = skill_repository.get_category_stats(db)
    return ok(data=stats).model_dump()


@router.get(
    "/catalog",
    summary="Browse the skill catalog with optional search filter",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def browse_skill_catalog(
    db: DbSession,
    q: str | None = Query(None, description="Search term to filter skills by name"),
    category: str | None = Query(None, description="Filter by skill category"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Return skills from the catalog, optionally filtered by name or category."""
    if q:
        skills = skill_repository.search(db, query=q, limit=limit)
    elif category:
        skills = skill_repository.get_by_category(db, category=category, skip=skip, limit=limit)
    else:
        skills = skill_repository.get_multi(db, skip=skip, limit=limit)

    return ok(
        data=[
            {
                "id": s.id,
                "name": s.name,
                "normalized_name": s.normalized_name,
                "category": s.category,
            }
            for s in skills
        ]
    ).model_dump()


@router.get(
    "/popular",
    summary="Get top skills ranked by candidate adoption",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_popular_skills(
    db: DbSession,
    limit: int = Query(10, ge=1, le=50, description="Max skills to return"),
) -> dict[str, Any]:
    """Retrieve skills ranked by how many candidates have added them to their profile."""
    skills = skill_repository.get_popular_skills(db, limit=limit)
    return ok(data=skills).model_dump()


@router.get(
    "/search",
    summary="Search skills by name with autocomplete support",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def search_skills(
    db: DbSession,
    q: str = Query(..., min_length=1, max_length=100, description="Partial skill name for autocomplete"),
    category: str | None = Query(None, description="Restrict search to a specific skill category"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
) -> dict[str, Any]:
    """Autocomplete skill names based on a partial query string, with optional category filter."""
    results = skill_repository.search(db, query=q, limit=limit)
    if category:
        results = [s for s in results if s.category == category]
    return ok(
        data=[
            {
                "id": s.id,
                "name": s.name,
                "normalized_name": s.normalized_name,
                "category": s.category,
            }
            for s in results
        ]
    ).model_dump()


@router.get(
    "/{skill_id}",
    summary="Get single skill by ID",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_skill(
    skill_id: int,
    db: DbSession,
) -> dict[str, Any]:
    """Retrieve details for a specific skill by its ID."""
    from fastapi import HTTPException
    skill = skill_repository.get(db, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with ID {skill_id} not found.",
        )
    return ok(
        data={
            "id": skill.id,
            "name": skill.name,
            "normalized_name": skill.normalized_name,
            "category": skill.category,
            "created_at": skill.created_at.isoformat() if skill.created_at else None,
        }
    ).model_dump()


@router.get(
    "/{skill_id}/demand",
    summary="Get market demand metrics for a specific skill",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_skill_demand(
    skill_id: int,
    db: DbSession,
) -> dict[str, Any]:
    """Retrieve market demand metrics including active job postings, target roles, and candidate counts."""
    from fastapi import HTTPException
    metrics = skill_repository.get_skill_demand_metrics(db, skill_id=skill_id)
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with ID {skill_id} not found.",
        )
    return ok(data=metrics).model_dump()


@router.get(
    "/{skill_id}/related",
    summary="Get related and co-occurring skills from job postings",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def get_related_skills(
    skill_id: int,
    db: DbSession,
    limit: int = Query(10, ge=1, le=50, description="Max related skills to return"),
) -> dict[str, Any]:
    """Retrieve skills that frequently co-occur with this skill across job postings."""
    from fastapi import HTTPException
    from sqlalchemy import func, select, distinct
    from app.models.associations import JobSkill
    from app.models.skill import Skill

    skill = skill_repository.get(db, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill with ID {skill_id} not found.",
        )

    job_subq = select(JobSkill.job_id).where(JobSkill.skill_id == skill_id).scalar_subquery()

    rows = db.execute(
        select(
            Skill.id,
            Skill.name,
            Skill.category,
            func.count(distinct(JobSkill.job_id)).label("co_occurrence_count"),
        )
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .where(JobSkill.job_id.in_(job_subq), JobSkill.skill_id != skill_id)
        .group_by(Skill.id, Skill.name, Skill.category)
        .order_by(func.count(distinct(JobSkill.job_id)).desc())
        .limit(limit)
    ).all()

    related = [
        {
            "skill_id": r.id,
            "name": r.name,
            "category": r.category,
            "co_occurrence_count": r.co_occurrence_count,
        }
        for r in rows
    ]
    return ok(
        data={
            "skill_id": skill.id,
            "skill_name": skill.name,
            "total_related": len(related),
            "related_skills": related,
        }
    ).model_dump()



@router.post(
    "/extract",
    summary="Extract technical skills from unstructured text",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def extract_skills_from_text(payload: SkillExtractionRequest) -> dict[str, Any]:
    """Parse job descriptions, resumes, or arbitrary text to identify technical competencies."""
    start_time = time.perf_counter()
    results = skill_extractor.extract_skills(
        payload.text,
        min_confidence=payload.min_confidence,
    )
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

    response_data = SkillExtractionResponse(
        total_extracted=len(results),
        skills=[SkillExtractionItemSchema(**s.to_dict()) for s in results],
        processing_time_ms=elapsed_ms,
    )
    return ok(data=response_data.model_dump()).model_dump()


@router.post(
    "/extract/batch",
    summary="Batch extract skills across multiple documents",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def extract_skills_batch(payload: BatchExtractionRequest) -> dict[str, Any]:
    """Parse multiple documents simultaneously and return consolidated skill metrics."""
    docs = [(doc.id, doc.text) for doc in payload.documents]
    report = batch_skill_extractor.extract_batch(
        docs,
        min_confidence=payload.min_confidence,
    )

    result_items = [
        BatchExtractionResultItem(
            id=r.doc_id,
            total_skills=r.total_skills,
            skills=[SkillExtractionItemSchema(**s.to_dict()) for s in r.skills],
        )
        for r in report.document_results
    ]

    response_data = BatchExtractionResponse(
        total_documents=report.total_documents,
        total_skills_found=report.total_skills_extracted,
        results=result_items,
        processing_time_ms=report.total_duration_ms,
    )
    return ok(data=response_data.model_dump()).model_dump()
