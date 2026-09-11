"""Unit tests for JobPosting SQLAlchemy ORM model."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.job import JobPosting


@pytest.fixture
def db_session():
    """Create a temporary in-memory database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestJobPostingModel:
    """Test suite for JobPosting model persistence and query operations."""

    def test_create_job_posting_with_defaults(self, db_session: Session) -> None:
        job = JobPosting(
            title="Senior Python Backend Engineer",
            company_name="Acme Tech",
            description="Build high-throughput REST APIs and microservices.",
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.id is not None
        assert job.title == "Senior Python Backend Engineer"
        assert job.company_name == "Acme Tech"
        assert job.is_remote is False
        assert job.employment_type == "full-time"
        assert job.experience_level == "mid"
        assert job.salary_currency == "USD"
        assert job.is_active is True
        assert job.posted_date is not None
        assert "Acme Tech" in repr(job)

    def test_create_full_job_posting(self, db_session: Session) -> None:
        now = datetime.now(timezone.utc)
        job = JobPosting(
            title="Lead ML Engineer",
            company_name="DeepAI Corp",
            location="Remote, USA",
            is_remote=True,
            employment_type="full-time",
            experience_level="lead",
            min_salary=180000.0,
            max_salary=240000.0,
            salary_currency="USD",
            description="Lead machine learning initiatives.",
            requirements_raw="Python, PyTorch, Kubernetes, MLOps",
            source_url="https://example.com/jobs/lead-ml",
            source_platform="linkedin",
            is_active=True,
            posted_date=now,
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        assert job.is_remote is True
        assert job.min_salary == 180000.0
        assert job.max_salary == 240000.0
        assert job.source_platform == "linkedin"

    def test_filter_active_remote_jobs(self, db_session: Session) -> None:
        db_session.add_all(
            [
                JobPosting(
                    title="Frontend Dev",
                    company_name="Co 1",
                    description="desc",
                    is_remote=True,
                    is_active=True,
                ),
                JobPosting(
                    title="Backend Dev",
                    company_name="Co 2",
                    description="desc",
                    is_remote=False,
                    is_active=True,
                ),
                JobPosting(
                    title="DevOps",
                    company_name="Co 3",
                    description="desc",
                    is_remote=True,
                    is_active=False,
                ),
            ]
        )
        db_session.commit()

        remote_active = (
            db_session.query(JobPosting)
            .filter_by(is_remote=True, is_active=True)
            .all()
        )
        assert len(remote_active) == 1
        assert remote_active[0].title == "Frontend Dev"
