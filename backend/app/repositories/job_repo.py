"""Job posting repository implementation."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import JobPosting
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[JobPosting]):
    """Data access repository for JobPosting entities."""

    def __init__(self) -> None:
        super().__init__(JobPosting)

    def get_active_jobs(
        self,
        db: Session,
        *,
        is_remote: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobPosting]:
        """Fetch active job postings with optional remote-only filtering."""
        stmt = select(JobPosting).where(JobPosting.is_active.is_(True))
        if is_remote is not None:
            stmt = stmt.where(JobPosting.is_remote.is_(is_remote))
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_by_company(
        self,
        db: Session,
        *,
        company_name: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobPosting]:
        """Fetch jobs posted by a specific company."""
        stmt = (
            select(JobPosting)
            .where(JobPosting.company_name.ilike(f"%{company_name}%"))
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())


job_repository = JobRepository()
