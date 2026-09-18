"""Integration tests for the /api/v1/roadmaps REST API endpoints."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.api.deps import get_db
from app.db.base import Base
import app.models  # noqa: F401
from app.main import create_application
from app.models.role import RoleSkillWeighting, TargetRole
from app.models.skill import Skill
from app.models.user import User
from app.services.user_skill_service import user_skill_service


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
def sample_setup(db_session: Session):
    user = User(email="api_learner@example.com", hashed_password="pw", full_name="API Learner")
    role = TargetRole(title="DevOps Engineer", slug="devops-engineer", category="Cloud")
    db_session.add_all([user, role])
    db_session.flush()

    s1 = Skill(name="Linux", normalized_name="linux")
    s2 = Skill(name="Docker", normalized_name="docker")
    s3 = Skill(name="Kubernetes", normalized_name="kubernetes")
    db_session.add_all([s1, s2, s3])
    db_session.flush()

    w1 = RoleSkillWeighting(role_id=role.id, skill_id=s1.id, weight=1.0)
    w2 = RoleSkillWeighting(role_id=role.id, skill_id=s2.id, weight=1.0)
    w3 = RoleSkillWeighting(role_id=role.id, skill_id=s3.id, weight=0.9)
    db_session.add_all([w1, w2, w3])
    db_session.commit()
    return {"user": user, "role": role}


class TestRoadmapEndpoints:
    def test_generate_transient_roadmap(self, api_client: TestClient):
        payload = {
            "missing_skills": ["Python", "FastAPI", "Docker"],
            "role_title": "Backend Developer",
            "weekly_commitment_hours": 10,
        }
        resp = api_client.post("/api/v1/roadmaps/generate", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["role_title"] == "Backend Developer"
        assert data["total_skills"] == 3
        assert len(data["phases"]) > 0

    def test_generate_roadmap_from_text(self, api_client: TestClient, sample_setup):
        payload = {
            "text": "Basic Linux skills and familiarity with bash.",
            "role_slug": "devops-engineer",
            "weekly_commitment_hours": 10,
        }
        resp = api_client.post("/api/v1/roadmaps/generate-from-text", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "roadmap" in body["data"]
        assert body["data"]["roadmap"]["role_title"] == "DevOps Engineer"

    def test_create_user_roadmap_and_get(self, api_client: TestClient, db_session: Session, sample_setup):
        user = sample_setup["user"]
        role = sample_setup["role"]

        # User has Linux
        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="Linux")

        create_resp = api_client.post(
            f"/api/v1/roadmaps/user/{user.id}?role_slug={role.slug}&weekly_commitment_hours=15"
        )
        assert create_resp.status_code == 201
        body = create_resp.json()
        assert body["success"] is True
        roadmap_id = body["data"]["id"]
        assert roadmap_id is not None

        # Fetch saved roadmap by id
        get_resp = api_client.get(f"/api/v1/roadmaps/{roadmap_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == roadmap_id
        assert len(get_resp.json()["data"]["milestones"]) > 0

        # List user roadmaps
        list_resp = api_client.get(f"/api/v1/roadmaps/user/{user.id}")
        assert list_resp.status_code == 200
        assert list_resp.json()["data"]["total"] >= 1

    def test_update_milestone_progress(self, api_client: TestClient, db_session: Session, sample_setup):
        user = sample_setup["user"]
        role = sample_setup["role"]

        create_resp = api_client.post(
            f"/api/v1/roadmaps/user/{user.id}?role_id={role.id}"
        )
        roadmap = create_resp.json()["data"]
        m_id = roadmap["milestones"][0]["id"]

        patch_resp = api_client.patch(
            f"/api/v1/roadmaps/{roadmap['id']}/milestones/{m_id}",
            json={"is_completed": True},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["data"]["is_completed"] is True
