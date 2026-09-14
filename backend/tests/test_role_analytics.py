"""Unit tests for the RoleAnalyzer service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401
from app.models.job import JobPosting
from app.schemas.enums import ExperienceLevel
from app.services.analytics.role_analyzer import RoleAnalyzer, role_analyzer


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        j1 = JobPosting(
            title="Senior Backend Engineer",
            company_name="A",
            description="desc",
            is_remote=True,
            experience_level=ExperienceLevel.SENIOR.value,
            is_active=True,
        )
        j2 = JobPosting(
            title="Junior Backend Developer",
            company_name="B",
            description="desc",
            is_remote=False,
            experience_level=ExperienceLevel.ENTRY.value,
            is_active=True,
        )
        j3 = JobPosting(
            title="Lead DevOps Engineer",
            company_name="C",
            description="desc",
            is_remote=True,
            experience_level=ExperienceLevel.LEAD.value,
            is_active=True,
        )
        session.add_all([j1, j2, j3])
        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestRoleAnalytics:
    """Test suite for role distribution and market share calculation."""

    def test_get_role_distributions(self, db_session) -> None:
        results = role_analyzer.get_role_distributions(db_session)
        assert len(results) >= 2

        backend_track = next(r for r in results if r.role_name == "Backend")
        assert backend_track.total_postings == 2
        assert backend_track.market_share_pct == round((2 / 3) * 100.0, 2)
        assert backend_track.remote_postings_count == 1
        assert backend_track.remote_pct == 50.0
        assert backend_track.seniority_breakdown[ExperienceLevel.SENIOR.value] == 1
        assert backend_track.seniority_breakdown[ExperienceLevel.ENTRY.value] == 1

        devops_track = next(r for r in results if r.role_name == "DevOps")
        assert devops_track.total_postings == 1
        assert devops_track.remote_pct == 100.0
