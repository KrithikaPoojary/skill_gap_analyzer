"""Job CRUD service layer.

Encapsulates business logic for creating, reading, updating, and deleting
job postings. Keeps route handlers thin by coordinating repository calls,
schema transformations, and domain validation.
"""

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.schemas.job import JobCreate, JobRead, JobUpdate
from app.schemas.job_filter import JobFilterParams
from app.schemas.pagination import PaginatedResponse, PaginationMeta, PaginationParams


class JobService:
    """Service layer for all job posting business operations."""

    def get_by_id(self, db: Session, job_id: int) -> JobPosting | None:
        """Fetch a single job posting by primary key."""
        return db.get(JobPosting, job_id)

    def get_paginated(
        self,
        db: Session,
        *,
        params: PaginationParams,
        filters: JobFilterParams | None = None,
    ) -> PaginatedResponse[JobRead]:
        """Fetch paginated job listings with optional filtering."""
        stmt = select(JobPosting)

        # Apply filters
        if filters:
            conditions = []
            if filters.is_active is not None:
                conditions.append(JobPosting.is_active.is_(filters.is_active))
            if filters.is_remote is not None:
                conditions.append(JobPosting.is_remote.is_(filters.is_remote))
            if filters.employment_type is not None:
                conditions.append(JobPosting.employment_type == filters.employment_type.value)
            if filters.experience_level is not None:
                conditions.append(JobPosting.experience_level == filters.experience_level.value)
            if filters.company_name:
                conditions.append(JobPosting.company_name.ilike(f"%{filters.company_name}%"))
            if filters.title:
                conditions.append(JobPosting.title.ilike(f"%{filters.title}%"))
            if filters.location:
                conditions.append(JobPosting.location.ilike(f"%{filters.location}%"))
            if filters.min_salary is not None:
                conditions.append(JobPosting.max_salary >= filters.min_salary)
            if filters.max_salary is not None:
                conditions.append(JobPosting.min_salary <= filters.max_salary)
            if filters.query:
                keyword = f"%{filters.query}%"
                conditions.append(
                    JobPosting.title.ilike(keyword) | JobPosting.description.ilike(keyword)
                )
            if conditions:
                stmt = stmt.where(and_(*conditions))

        # Count total matching records
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        # Fetch page
        stmt = stmt.offset(params.offset).limit(params.limit)
        jobs = list(db.scalars(stmt).all())

        meta = PaginationMeta.create(
            total_items=total,
            page=params.page,
            page_size=params.page_size,
        )

        items = [JobRead.model_validate(job) for job in jobs]
        return PaginatedResponse[JobRead](items=items, pagination=meta)

    def create(self, db: Session, *, payload: JobCreate) -> JobPosting:
        """Create a new job posting and persist associated skill requirements."""
        job_data = payload.model_dump(exclude={"skills"})
        job = JobPosting(**job_data)
        db.add(job)
        db.flush()  # Obtain job.id before adding associations

        for skill_req in payload.skills:
            job_skill = JobSkill(
                job_id=job.id,
                skill_id=skill_req.skill_id,
                is_required=skill_req.is_required,
                importance_weight=skill_req.importance_weight,
            )
            db.add(job_skill)

        db.commit()
        db.refresh(job)
        return job

    def update(self, db: Session, *, job: JobPosting, payload: JobUpdate) -> JobPosting:
        """Apply partial updates to an existing job posting."""
        update_data = payload.model_dump(exclude_unset=True, exclude={"skills"})
        for field, value in update_data.items():
            if hasattr(job, field):
                setattr(job, field, value)

        if payload.skills is not None:
            # Replace all existing skill associations
            for existing in list(job.job_skills):
                db.delete(existing)
            db.flush()
            for skill_req in payload.skills:
                db.add(
                    JobSkill(
                        job_id=job.id,
                        skill_id=skill_req.skill_id,
                        is_required=skill_req.is_required,
                        importance_weight=skill_req.importance_weight,
                    )
                )

        db.commit()
        db.refresh(job)
        return job

    def delete(self, db: Session, *, job_id: int) -> JobPosting | None:
        """Soft-delete a job posting by setting is_active=False."""
        job = db.get(JobPosting, job_id)
        if job is None:
            return None
        job.is_active = False
        db.commit()
        db.refresh(job)
        return job


job_service = JobService()
