"""Integration tests for the /api/v1/profile REST API endpoints."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.api.deps import get_db
from app.db.base import Base
import app.models  # noqa: F401
from app.main import create_application
from app.models.user import User


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def api_client(db_session: Session) -> TestClient:
    app = create_application()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_user(db_session: Session) -> User:
    user = User(
        email="api_dev@example.com",
        hashed_password="pw_hash_test",
        full_name="Api Developer",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestProfileEndpoints:
    def test_get_profile_not_found(self, api_client: TestClient):
        resp = api_client.get("/api/v1/profile/999")
        assert resp.status_code == 404

    def test_upsert_profile(self, api_client: TestClient, sample_user: User):
        payload = {
            "headline": "Lead Systems Architect",
            "bio": "Specialized in event-driven systems.",
            "current_title": "Staff Engineer",
            "years_of_experience": 10.0,
            "location": "Remote - US",
            "github_url": "https://github.com/apidev",
        }
        resp = api_client.put(f"/api/v1/profile/{sample_user.id}", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["headline"] == "Lead Systems Architect"
        assert body["data"]["years_of_experience"] == 10.0

    def test_add_user_skill(self, api_client: TestClient, sample_user: User):
        payload = {
            "skill_name": "Kubernetes",
            "proficiency_level": "advanced",
            "years_of_experience": 4.0,
            "is_verified": False,
        }
        resp = api_client.post(f"/api/v1/profile/{sample_user.id}/skills", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["name"] == "Kubernetes"
        assert body["data"]["proficiency_level"] == "advanced"

    def test_bulk_add_user_skills(self, api_client: TestClient, sample_user: User):
        payload = {
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "proficiency_level": "intermediate",
        }
        resp = api_client.post(f"/api/v1/profile/{sample_user.id}/skills/bulk", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["added_count"] == 3

    def test_get_full_profile_after_creation(self, api_client: TestClient, sample_user: User):
        # 1. Update profile
        api_client.put(
            f"/api/v1/profile/{sample_user.id}",
            json={"headline": "Fullstack Cloud Developer", "years_of_experience": 5.0},
        )
        # 2. Add skill
        api_client.post(
            f"/api/v1/profile/{sample_user.id}/skills",
            json={"skill_name": "Go", "proficiency_level": "intermediate"},
        )
        # 3. Fetch
        resp = api_client.get(f"/api/v1/profile/{sample_user.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["email"] == "api_dev@example.com"
        assert data["profile"]["headline"] == "Fullstack Cloud Developer"
        assert len(data["skills"]) == 1
        assert data["skills"][0]["name"] == "Go"

    def test_remove_user_skill(self, api_client: TestClient, sample_user: User):
        # Add skill
        add_resp = api_client.post(
            f"/api/v1/profile/{sample_user.id}/skills",
            json={"skill_name": "Rust", "proficiency_level": "beginner"},
        )
        skill_id = add_resp.json()["data"]["skill_id"]

        # Delete
        del_resp = api_client.delete(f"/api/v1/profile/{sample_user.id}/skills/{skill_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["data"]["removed"] is True

        # Delete non-existent
        del_again = api_client.delete(f"/api/v1/profile/{sample_user.id}/skills/{skill_id}")
        assert del_again.status_code == 404
