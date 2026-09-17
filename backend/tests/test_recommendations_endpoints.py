"""Integration tests for the /api/v1/recommendations REST API endpoints."""

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
def setup_roles(db_session: Session):
    s_py = Skill(name="Python", normalized_name="python", category="language")
    s_fastapi = Skill(name="FastAPI", normalized_name="fastapi", category="framework")
    s_docker = Skill(name="Docker", normalized_name="docker", category="cloud_devops")
    s_tf = Skill(name="TensorFlow", normalized_name="tensorflow", category="ai_ml")
    db_session.add_all([s_py, s_fastapi, s_docker, s_tf])
    db_session.flush()

    role_backend = TargetRole(
        title="Backend API Developer",
        slug="backend-api-dev",
        category="Software Engineering",
    )
    role_ml = TargetRole(
        title="Machine Learning Engineer",
        slug="ml-engineer",
        category="AI & ML",
    )
    db_session.add_all([role_backend, role_ml])
    db_session.flush()

    w1 = RoleSkillWeighting(role_id=role_backend.id, skill_id=s_py.id, weight=1.0, is_core=True)
    w2 = RoleSkillWeighting(role_id=role_backend.id, skill_id=s_fastapi.id, weight=0.9, is_core=True)
    w3 = RoleSkillWeighting(role_id=role_backend.id, skill_id=s_docker.id, weight=0.8, is_core=False)

    w4 = RoleSkillWeighting(role_id=role_ml.id, skill_id=s_py.id, weight=1.0, is_core=True)
    w5 = RoleSkillWeighting(role_id=role_ml.id, skill_id=s_tf.id, weight=1.0, is_core=True)

    db_session.add_all([w1, w2, w3, w4, w5])
    db_session.commit()


class TestRecommendationsEndpoints:
    def test_recommendations_from_skills(self, api_client: TestClient, setup_roles):
        payload = {
            "skills": ["Python", "FastAPI"],
            "limit": 5,
        }
        resp = api_client.post("/api/v1/recommendations/from-skills", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        recs = body["data"]["recommendations"]
        assert len(recs) == 2
        # Backend API Developer should rank #1
        assert recs[0]["title"] == "Backend API Developer"
        assert recs[0]["match_score"] > recs[1]["match_score"]

    def test_recommendations_from_text(self, api_client: TestClient, setup_roles):
        payload = {
            "text": "Deep learning practitioner working with Python and TensorFlow on neural networks.",
            "limit": 3,
        }
        resp = api_client.post("/api/v1/recommendations/from-text", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert "extracted_skills" in data
        assert "recommendations" in data
        recs = data["recommendations"]
        assert recs[0]["title"] == "Machine Learning Engineer"
        assert recs[0]["match_score"] == 1.0

    def test_user_recommendations(self, api_client: TestClient, db_session: Session, setup_roles):
        user = User(email="rec_user@test.com", hashed_password="pw", full_name="Rec User")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="Python")
        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="Docker")

        resp = api_client.get(f"/api/v1/recommendations/user/{user.id}?limit=2")
        assert resp.status_code == 200
        recs = resp.json()["data"]["recommendations"]
        assert len(recs) > 0
        assert recs[0]["title"] == "Backend API Developer"

    def test_user_recommendations_not_found(self, api_client: TestClient):
        resp = api_client.get("/api/v1/recommendations/user/999")
        assert resp.status_code == 404
