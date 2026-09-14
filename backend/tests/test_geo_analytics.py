"""Unit tests for the GeoAnalyzer service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401
from app.models.job import JobPosting
from app.schemas.enums import ExperienceLevel
from app.services.analytics.geo_analyzer import GeoAnalyzer, geo_analyzer


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
            title="Backend Dev",
            company_name="A",
            location="San Francisco, CA",
            description="desc",
            is_remote=False,
            experience_level=ExperienceLevel.MID.value,
            is_active=True,
        )
        j2 = JobPosting(
            title="Frontend Dev",
            company_name="B",
            location="San Francisco, CA",
            description="desc",
            is_remote=True,
            experience_level=ExperienceLevel.MID.value,
            is_active=True,
        )
        j3 = JobPosting(
            title="DevOps Lead",
            company_name="C",
            location="Remote",
            description="desc",
            is_remote=True,
            experience_level=ExperienceLevel.SENIOR.value,
            is_active=True,
        )
        session.add_all([j1, j2, j3])
        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestGeoAnalytics:
    """Test suite for location market share and remote ratio calculations."""

    def test_get_top_locations(self, db_session) -> None:
        locations = geo_analyzer.get_top_locations(db_session, limit=5)
        assert len(locations) == 2

        sf = next(loc for loc in locations if loc.location_name == "San Francisco, CA")
        assert sf.total_postings == 2
        assert sf.market_share_pct == round((2 / 3) * 100.0, 2)
        assert sf.remote_postings_count == 1
        assert sf.remote_pct == 50.0

    def test_get_remote_summary(self, db_session) -> None:
        summary = geo_analyzer.get_remote_summary(db_session)
        assert summary.total_active_jobs == 3
        assert summary.total_remote_jobs == 2
        assert summary.overall_remote_pct == round((2 / 3) * 100.0, 2)
        assert summary.remote_by_seniority[ExperienceLevel.MID.value] == 50.0
        assert summary.remote_by_seniority[ExperienceLevel.SENIOR.value] == 100.0
