"""Integration tests for the JobService CRUD operations."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.skill import Skill, SkillCategory
from app.schemas.enums import EmploymentType, ExperienceLevel, SourcePlatform
from app.schemas.job import JobCreate, JobUpdate
from app.schemas.job_filter import JobFilterParams
from app.schemas.pagination import PaginationParams
from app.schemas.skill import JobSkillCreate
from app.services.job_service import JobService


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite session for service integration tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def service() -> JobService:
    return JobService()


@pytest.fixture
def seed_skill(db_session: Session) -> Skill:
    """Persist a test skill to be used in JobSkill associations."""
    skill = Skill(name="Python", normalized_name="python", category=SkillCategory.LANGUAGE.value)
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)
    return skill


class TestJobServiceCreate:
    """Integration tests for job creation via service."""

    def test_create_minimal_job(self, db_session: Session, service: JobService) -> None:
        payload = JobCreate(
            title="Backend Engineer",
            company_name="StartupCo",
            description="Build scalable Python services.",
        )
        job = service.create(db_session, payload=payload)
        assert job.id is not None
        assert job.title == "Backend Engineer"
        assert job.employment_type == "full_time"
        assert job.is_active is True

    def test_create_job_with_skills(
        self, db_session: Session, service: JobService, seed_skill: Skill
    ) -> None:
        payload = JobCreate(
            title="Senior Python Dev",
            company_name="BigTech",
            description="Design distributed backend systems.",
            skills=[JobSkillCreate(skill_id=seed_skill.id, is_required=True, importance_weight=4.0)],
        )
        job = service.create(db_session, payload=payload)
        db_session.refresh(job)
        assert len(job.job_skills) == 1
        assert job.job_skills[0].skill_id == seed_skill.id
        assert job.job_skills[0].importance_weight == 4.0


class TestJobServiceRead:
    """Integration tests for paginated listing and filtering."""

    def _seed_jobs(self, db_session: Session, service: JobService) -> None:
        jobs = [
            JobCreate(
                title="Python Backend Engineer",
                company_name="Alpha Corp",
                description="Build REST APIs with FastAPI.",
                is_remote=True,
                experience_level=ExperienceLevel.SENIOR,
                min_salary=120000.0,
                max_salary=160000.0,
            ),
            JobCreate(
                title="Frontend Developer",
                company_name="Beta Inc",
                description="React web applications.",
                is_remote=False,
                experience_level=ExperienceLevel.MID,
                min_salary=80000.0,
                max_salary=110000.0,
            ),
            JobCreate(
                title="DevOps Specialist",
                company_name="Gamma Ltd",
                description="CI/CD pipelines and cloud infra.",
                is_remote=True,
                experience_level=ExperienceLevel.LEAD,
                is_active=True,
            ),
        ]
        for j in jobs:
            service.create(db_session, payload=j)

    def test_list_all_active_jobs(self, db_session: Session, service: JobService) -> None:
        self._seed_jobs(db_session, service)
        params = PaginationParams(page=1, page_size=10)
        result = service.get_paginated(db_session, params=params)
        assert result.pagination.total_items == 3
        assert len(result.items) == 3

    def test_filter_by_remote(self, db_session: Session, service: JobService) -> None:
        self._seed_jobs(db_session, service)
        params = PaginationParams()
        filters = JobFilterParams(is_remote=True)
        result = service.get_paginated(db_session, params=params, filters=filters)
        assert result.pagination.total_items == 2
        for item in result.items:
            assert item.is_remote is True

    def test_filter_by_keyword(self, db_session: Session, service: JobService) -> None:
        self._seed_jobs(db_session, service)
        filters = JobFilterParams(query="Python")
        result = service.get_paginated(db_session, params=PaginationParams(), filters=filters)
        assert result.pagination.total_items == 1
        assert "Python" in result.items[0].title

    def test_pagination_navigation(self, db_session: Session, service: JobService) -> None:
        self._seed_jobs(db_session, service)
        params = PaginationParams(page=1, page_size=2)
        result = service.get_paginated(db_session, params=params)
        assert len(result.items) == 2
        assert result.pagination.has_next is True
        assert result.pagination.has_prev is False


class TestJobServiceUpdate:
    """Integration tests for partial update operations."""

    def test_partial_update_title(self, db_session: Session, service: JobService) -> None:
        job = service.create(
            db_session,
            payload=JobCreate(
                title="Junior Dev", company_name="Co", description="Entry level Python dev role."
            ),
        )
        updated = service.update(
            db_session, job=job, payload=JobUpdate(title="Mid-Level Dev")
        )
        assert updated.title == "Mid-Level Dev"
        assert updated.company_name == "Co"

    def test_soft_delete(self, db_session: Session, service: JobService) -> None:
        job = service.create(
            db_session,
            payload=JobCreate(
                title="Contract Dev", company_name="Co", description="Short contract role."
            ),
        )
        assert job.is_active is True
        deleted = service.delete(db_session, job_id=job.id)
        assert deleted is not None
        assert deleted.is_active is False

    def test_delete_non_existent_returns_none(self, db_session: Session, service: JobService) -> None:
        result = service.delete(db_session, job_id=9999)
        assert result is None
