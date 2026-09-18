"""Unit tests for RoadmapService."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.role import RoleSkillWeighting, TargetRole
from app.models.skill import Skill
from app.models.user import User
from app.services.roadmap_service import roadmap_service
from app.services.user_skill_service import user_skill_service


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session: Session) -> User:
    user = User(email="learner_bob@example.com", hashed_password="pw", full_name="Learner Bob")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seeded_role(db_session: Session) -> TargetRole:
    role = TargetRole(
        title="Backend Engineer",
        slug="backend-engineer",
        category="Software Engineering",
    )
    db_session.add(role)
    db_session.flush()

    s_py = Skill(name="Python", normalized_name="python")
    s_fastapi = Skill(name="FastAPI", normalized_name="fastapi")
    s_docker = Skill(name="Docker", normalized_name="docker")
    db_session.add_all([s_py, s_fastapi, s_docker])
    db_session.flush()

    w1 = RoleSkillWeighting(role_id=role.id, skill_id=s_py.id, weight=1.0)
    w2 = RoleSkillWeighting(role_id=role.id, skill_id=s_fastapi.id, weight=0.9)
    w3 = RoleSkillWeighting(role_id=role.id, skill_id=s_docker.id, weight=0.8)
    db_session.add_all([w1, w2, w3])
    db_session.commit()
    db_session.refresh(role)
    return role


class TestRoadmapService:
    def test_generate_transient(self):
        result = roadmap_service.generate_transient(
            missing_skills=["Python", "FastAPI", "Docker"],
            role_title="API Specialist",
            weekly_commitment_hours=10,
        )
        assert result["role_title"] == "API Specialist"
        assert result["total_skills"] == 3
        assert result["total_estimated_hours"] > 0
        assert len(result["phases"]) > 0

    def test_generate_from_text(self, db_session: Session, seeded_role: TargetRole):
        # Text only mentions Python -> Missing should include FastAPI and Docker
        result = roadmap_service.generate_from_text(
            db_session,
            text="Experienced in Python scripting.",
            role_slug="backend-engineer",
            weekly_commitment_hours=10,
        )
        assert "extracted_skills" in result
        assert "gap_report" in result
        assert "roadmap" in result
        rm = result["roadmap"]
        assert rm["role_title"] == "Backend Engineer"
        # At least FastAPI or Docker in roadmap
        all_skills = [s["name"] for p in rm["phases"] for s in p["skills"]]
        assert "FastAPI" in all_skills or "Docker" in all_skills

    def test_create_and_persist_for_user(
        self, db_session: Session, test_user: User, seeded_role: TargetRole
    ):
        # User has Python
        user_skill_service.add_user_skill(db_session, user_id=test_user.id, skill_name="Python")

        saved = roadmap_service.create_and_persist_for_user(
            db_session,
            user_id=test_user.id,
            role_slug="backend-engineer",
            weekly_commitment_hours=12,
        )
        assert saved["id"] is not None
        assert saved["user_id"] == test_user.id
        assert saved["target_role_name"] == "Backend Engineer"
        assert len(saved["milestones"]) > 0

        # Query user roadmaps
        user_rms = roadmap_service.get_user_roadmaps(db_session, user_id=test_user.id)
        assert len(user_rms) == 1
        assert user_rms[0]["id"] == saved["id"]

    def test_update_milestone_progress(
        self, db_session: Session, test_user: User, seeded_role: TargetRole
    ):
        saved = roadmap_service.create_and_persist_for_user(
            db_session,
            user_id=test_user.id,
            role_slug="backend-engineer",
        )
        m_id = saved["milestones"][0]["id"]

        updated = roadmap_service.update_milestone_progress(
            db_session, milestone_id=m_id, is_completed=True
        )
        assert updated is not None
        assert updated["is_completed"] is True
