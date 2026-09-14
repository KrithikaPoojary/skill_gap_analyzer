"""Integration tests for the /api/v1/analytics REST API endpoints."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.api.deps import get_db
from app.db.base import Base
import app.models  # noqa: F401
from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill
from app.schemas.enums import ExperienceLevel
from app.main import create_application


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
            location="San Francisco, CA",
            is_remote=True,
            experience_level=ExperienceLevel.SENIOR.value,
            min_salary=130000.0,
            max_salary=170000.0,
            description="High-scale distributed systems.",
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


@pytest.fixture
def api_client(db_session):
    app = create_application()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client


class TestAnalyticsEndpoints:
    """Test suite for analytics HTTP endpoints."""

    def test_get_market_overview(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_active_jobs"] == 1
        assert data["total_skills_tracked"] == 1
        assert data["overall_remote_pct"] == 100.0
        assert len(data["top_skills"]) == 1
        assert data["top_skills"][0]["skill_name"] == "Python"

    def test_get_skills_analytics(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/analytics/skills?limit=5")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "top_skills" in data
        assert "category_distribution" in data
        assert len(data["top_skills"]) == 1

    def test_get_roles_analytics(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/analytics/roles")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        backend = next(r for r in data if r["role_name"] == "Backend")
        assert backend["total_postings"] == 1
        assert backend["remote_pct"] == 100.0

    def test_get_salaries_analytics(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/analytics/salaries")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "by_experience" in data
        assert "by_role" in data
        assert "remote_vs_onsite" in data

    def test_get_geo_analytics(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/analytics/geo")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "top_locations" in data
        assert "remote_summary" in data
        assert data["remote_summary"]["overall_remote_pct"] == 100.0
