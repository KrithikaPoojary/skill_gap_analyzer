"""Integration tests for the /api/v1/gap-analysis REST API endpoints."""

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
def setup_role(db_session: Session) -> TargetRole:
    role = TargetRole(
        title="Full Stack Engineer",
        slug="full-stack-engineer",
        category="Software Engineering",
        min_experience_years=3.0,
    )
    db_session.add(role)
    db_session.flush()

    s1 = Skill(name="Python", normalized_name="python", category="language")
    s2 = Skill(name="React", normalized_name="react", category="framework")
    s3 = Skill(name="PostgreSQL", normalized_name="postgresql", category="database")
    db_session.add_all([s1, s2, s3])
    db_session.flush()

    w1 = RoleSkillWeighting(role_id=role.id, skill_id=s1.id, weight=1.0, is_core=True)
    w2 = RoleSkillWeighting(role_id=role.id, skill_id=s2.id, weight=1.0, is_core=True)
    w3 = RoleSkillWeighting(role_id=role.id, skill_id=s3.id, weight=0.8, is_core=False)
    db_session.add_all([w1, w2, w3])
    db_session.commit()
    db_session.refresh(role)
    return role


class TestGapAnalysisEndpoints:
    def test_analyse_skill_gap_success(self, api_client: TestClient, setup_role: TargetRole):
        payload = {
            "skills": ["Python", "React", "Git"],
            "role_slug": "full-stack-engineer",
        }
        resp = api_client.post("/api/v1/gap-analysis/analyse", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert data["role_name"] == "Full Stack Engineer"
        assert set(data["matched_skills"]) == {"Python", "React"}
        assert any(s["name"] == "PostgreSQL" for s in data["missing_skills"])
        assert data["coverage_pct"] > 60.0

    def test_analyse_gap_from_text(self, api_client: TestClient, setup_role: TargetRole):
        payload = {
            "text": "Expert in Python web development with React frontends.",
            "role_name": "Full Stack Engineer",
        }
        resp = api_client.post("/api/v1/gap-analysis/analyse-from-text", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        data = body["data"]
        assert "extracted_skills" in data
        assert "gap_report" in data
        report = data["gap_report"]
        assert "Python" in report["matched_skills"]
        assert "React" in report["matched_skills"]

    def test_user_gap_analysis_endpoint(
        self, api_client: TestClient, db_session: Session, setup_role: TargetRole
    ):
        user = User(email="analyst@test.com", hashed_password="pw", full_name="User Analyst")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="Python")
        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="PostgreSQL")

        resp = api_client.get(
            f"/api/v1/gap-analysis/user/{user.id}?role_slug=full-stack-engineer"
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert set(data["matched_skills"]) == {"Python", "PostgreSQL"}
        assert any(s["name"] == "React" for s in data["missing_skills"])

    def test_user_gap_analysis_missing_role_params(
        self, api_client: TestClient, db_session: Session
    ):
        user = User(email="test2@test.com", hashed_password="pw")
        db_session.add(user)
        db_session.commit()

        resp = api_client.get(f"/api/v1/gap-analysis/user/{user.id}")
        assert resp.status_code == 400
