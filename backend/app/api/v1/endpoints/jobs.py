"""Job postings REST API endpoints.

Provides CRUD endpoints for managing job market postings with
full pagination, filtering, validation, and soft-delete support.
"""

from typing import Any
import uuid

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import DbSession
from app.schemas.enums import EmploymentType, ExperienceLevel
from app.schemas.job import JobCreate, JobRead, JobUpdate
from app.schemas.job_filter import JobFilterParams
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.response import ok
from app.services.ingestion_service import ingestion_service
from app.services.ingestion_telemetry import ingestion_telemetry
from app.services.job_service import job_service

router = APIRouter(prefix="/jobs", tags=["Job Postings"])


class IngestBatchPayload(BaseModel):
    """Payload for batch ingesting job records via API."""

    records: list[dict[str, Any]] = Field(default_factory=list, description="Raw job postings to ingest")
    batch_size: int = Field(50, ge=1, le=500, description="Commit batch size")
    dry_run: bool = Field(False, description="Simulate without persisting")


@router.post(
    "",
    summary="Create a new job posting",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
def create_job(
    payload: JobCreate,
    db: DbSession,
) -> dict:
    """Create and persist a new job posting with optional skill requirements."""
    job = job_service.create(db, payload=payload)
    return ok(data=JobRead.model_validate(job).model_dump()).model_dump()


@router.get(
    "",
    summary="List job postings with pagination and filtering",
    response_model=dict,
)
def list_jobs(
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    query: str | None = Query(None, description="Full-text keyword search"),
    title: str | None = Query(None, description="Partial title filter"),
    company_name: str | None = Query(None, description="Company name filter"),
    location: str | None = Query(None, description="Location filter"),
    is_remote: bool | None = Query(None, description="Remote position filter"),
    employment_type: EmploymentType | None = Query(None, description="Employment type"),
    experience_level: ExperienceLevel | None = Query(None, description="Seniority level"),
    min_salary: float | None = Query(None, ge=0, description="Minimum salary threshold"),
    max_salary: float | None = Query(None, ge=0, description="Maximum salary threshold"),
    is_active: bool | None = Query(True, description="Active listings only"),
) -> dict:
    """List all job postings with optional filters and pagination."""
    params = PaginationParams(page=page, page_size=page_size)
    filters = JobFilterParams(
        query=query,
        title=title,
        company_name=company_name,
        location=location,
        is_remote=is_remote,
        employment_type=employment_type,
        experience_level=experience_level,
        min_salary=min_salary,
        max_salary=max_salary,
        is_active=is_active,
    )
    result = job_service.get_paginated(db, params=params, filters=filters)
    return ok(data=result.model_dump()).model_dump()


@router.post(
    "/ingest",
    summary="Batch ingest raw job postings",
    status_code=status.HTTP_200_OK,
    response_model=dict,
)
def ingest_jobs_batch(
    payload: IngestBatchPayload,
    db: DbSession,
) -> dict:
    """Batch ingest a list of raw job records with automatic normalization and deduplication."""
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    report = ingestion_service.ingest_records(
        db,
        records=payload.records,
        batch_size=payload.batch_size,
        dry_run=payload.dry_run,
    )
    if not payload.dry_run:
        ingestion_telemetry.record_run(
            run_id=run_id,
            source_name="api_batch_upload",
            total=report.total_records,
            inserted=report.inserted_records,
            skipped=report.skipped_records,
            errors=report.error_records,
            duration=report.duration_seconds,
        )
    return ok(data=report.to_dict()).model_dump()


@router.get(
    "/ingest/telemetry",
    summary="Get recent ingestion telemetry metrics",
    response_model=dict,
)
def get_ingestion_telemetry(
    limit: int = Query(10, ge=1, le=50, description="Max runs to return"),
) -> dict:
    """Retrieve history and summary metrics for recent dataset ingestion runs."""
    recent = ingestion_telemetry.get_recent(limit=limit)
    stats = ingestion_telemetry.get_summary_stats()
    return ok(data={"recent_runs": recent, "summary": stats}).model_dump()


@router.get(
    "/{job_id}",
    summary="Retrieve a single job posting by ID",
    response_model=dict,
)
def get_job(job_id: int, db: DbSession) -> dict:
    """Fetch a job posting by primary key."""
    job = job_service.get_by_id(db, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job posting with id {job_id} not found",
        )
    return ok(data=JobRead.model_validate(job).model_dump()).model_dump()


@router.patch(
    "/{job_id}",
    summary="Partially update a job posting",
    response_model=dict,
)
def update_job(job_id: int, payload: JobUpdate, db: DbSession) -> dict:
    """Apply partial updates to an existing job posting."""
    job = job_service.get_by_id(db, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job posting with id {job_id} not found",
        )
    updated = job_service.update(db, job=job, payload=payload)
    return ok(data=JobRead.model_validate(updated).model_dump()).model_dump()


@router.delete(
    "/{job_id}",
    summary="Soft delete a job posting",
    response_model=dict,
)
def delete_job(job_id: int, db: DbSession) -> dict:
    """Deactivate a job posting (soft delete by setting is_active=False)."""
    deleted = job_service.delete(db, job_id=job_id)
    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job posting with id {job_id} not found",
        )
    return ok(
        data={"id": deleted.id, "is_active": deleted.is_active, "message": "Job posting deactivated"}
    ).model_dump()
