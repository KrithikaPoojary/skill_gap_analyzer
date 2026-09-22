"""Repository layer for user saved jobs and recruitment application tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.job import JobPosting
from app.models.saved_job import ApplicationStatus, UserSavedJob


class SavedJobRepository:
    """Encapsulates database operations for bookmarked jobs and application tracking."""

    def get_by_user_and_job(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
    ) -> UserSavedJob | None:
        """Find a single bookmark record for a user and job."""
        stmt = (
            select(UserSavedJob)
            .where(UserSavedJob.user_id == user_id, UserSavedJob.job_id == job_id)
            .options(joinedload(UserSavedJob.job))
        )
        return db.scalar(stmt)

    def list_by_user(
        self,
        db: Session,
        *,
        user_id: int,
        status: ApplicationStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[UserSavedJob]:
        """Fetch paginated list of saved jobs for a specific candidate."""
        stmt = (
            select(UserSavedJob)
            .where(UserSavedJob.user_id == user_id)
            .options(joinedload(UserSavedJob.job))
            .order_by(UserSavedJob.created_at.desc())
        )
        if status:
            stmt = stmt.where(UserSavedJob.status == status)
        stmt = stmt.offset(offset).limit(limit)
        return list(db.scalars(stmt).unique().all())

    def count_by_user(
        self,
        db: Session,
        *,
        user_id: int,
        status: ApplicationStatus | None = None,
    ) -> int:
        """Count total saved jobs for a candidate."""
        stmt = select(func.count(UserSavedJob.id)).where(UserSavedJob.user_id == user_id)
        if status:
            stmt = stmt.where(UserSavedJob.status == status)
        return db.scalar(stmt) or 0

    def save_job(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
        notes: str | None = None,
    ) -> UserSavedJob:
        """Bookmark a job posting for a candidate."""
        existing = self.get_by_user_and_job(db, user_id=user_id, job_id=job_id)
        if existing:
            if notes is not None:
                existing.notes = notes
            db.commit()
            db.refresh(existing)
            return existing

        saved = UserSavedJob(
            user_id=user_id,
            job_id=job_id,
            status=ApplicationStatus.SAVED,
            notes=notes,
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)
        return saved

    def update_status(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
        status: ApplicationStatus,
        notes: str | None = None,
    ) -> UserSavedJob | None:
        """Update application status (applied, interviewing, offered, rejected)."""
        record = self.get_by_user_and_job(db, user_id=user_id, job_id=job_id)
        if not record:
            return None

        record.status = status
        if status == ApplicationStatus.APPLIED and not record.applied_at:
            record.applied_at = datetime.now(timezone.utc)
        if notes is not None:
            record.notes = notes

        db.commit()
        db.refresh(record)
        return record

    def remove_saved_job(
        self,
        db: Session,
        *,
        user_id: int,
        job_id: int,
    ) -> bool:
        """Remove a job from user's bookmarks."""
        record = self.get_by_user_and_job(db, user_id=user_id, job_id=job_id)
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True


saved_job_repository = SavedJobRepository()
