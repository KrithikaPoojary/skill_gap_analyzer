"""Unit tests for the centralized AnalyticsService."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401
from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill
from app.schemas.analytics import MarketOverviewSchema
from app.schemas.enums import ExperienceLevel
from app.services.analytics_service import AnalyticsService, analytics_service


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
        s = Skill(name="Python", normalized_name="python", category="language")
        session.add(s)
        session.flush()

        j = JobPosting(
            title="Senior Backend Engineer",
            company_name="Acme Corp",
            location="Seattle, WA",
            is_remote=True,
            experience_level=ExperienceLevel.SENIOR.value,
            min_salary=140000.0,
            max_salary=180000.0,
            description="desc",
            is_active=True,
        )
        session.add(j)
        session.flush()

        js = JobSkill(job_id=j.id, skill_id=s.id, is_required=True)
        session.add(js)
        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestAnalyticsService:
    """Test suite for top-level analytics service operations."""

    def test_get_market_overview(self, db_session) -> None:
        overview = analytics_service.get_market_overview(db_session)
        assert isinstance(overview, MarketOverviewSchema)
        assert overview.total_active_jobs == 1
        assert overview.total_skills_tracked == 1
        assert overview.overall_remote_pct == 100.0
        assert len(overview.top_skills) == 1
        assert overview.top_skills[0].skill_name == "Python"
        assert len(overview.top_roles) == 1
        assert overview.top_roles[0].role_name == "Backend"

    def test_get_skills_analysis(self, db_session) -> None:
        res = analytics_service.get_skills_analysis(db_session)
        assert "top_skills" in res
        assert "category_distribution" in res
        assert len(res["top_skills"]) == 1

    def test_get_salary_analysis(self, db_session) -> None:
        res = analytics_service.get_salary_analysis(db_session)
        assert "by_experience" in res
        assert "by_role" in res
        assert "remote_vs_onsite" in res

    def test_get_geo_analysis(self, db_session) -> None:
        res = analytics_service.get_geo_analysis(db_session)
        assert "top_locations" in res
        assert "remote_summary" in res
        assert res["remote_summary"]["overall_remote_pct"] == 100.0
