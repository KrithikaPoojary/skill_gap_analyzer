"""Unit tests for RecommendationService."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.role import RoleSkillWeighting, TargetRole
from app.models.skill import Skill
from app.models.user import User
from app.services.recommendation_service import recommendation_service
from app.services.user_skill_service import user_skill_service


@pytest.fixture
def db_session():
    """In-memory SQLite database session."""
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
def seeded_roles_and_skills(db_session: Session) -> dict[str, TargetRole]:
    """Seed skills and two different target roles: Backend vs Data Science."""
    s_py = Skill(name="Python", normalized_name="python", category="language")
    s_sql = Skill(name="PostgreSQL", normalized_name="postgresql", category="database")
    s_dock = Skill(name="Docker", normalized_name="docker", category="cloud_devops")
    s_pd = Skill(name="Pandas", normalized_name="pandas", category="ai_ml")
    s_torch = Skill(name="PyTorch", normalized_name="pytorch", category="ai_ml")
    db_session.add_all([s_py, s_sql, s_dock, s_pd, s_torch])
    db_session.flush()

    # Role 1: Backend Developer
    backend_role = TargetRole(
        title="Backend Developer",
        slug="backend-developer",
        category="Software Engineering",
        min_experience_years=2.0,
    )
    # Role 2: Data Scientist
    ds_role = TargetRole(
        title="Data Scientist",
        slug="data-scientist",
        category="Data & AI",
        min_experience_years=3.0,
    )
    db_session.add_all([backend_role, ds_role])
    db_session.flush()

    # Backend skills: Python (1.0), PostgreSQL (0.9), Docker (0.8)
    # DS skills: Python (1.0), Pandas (0.9), PyTorch (0.8)
    weights = [
        RoleSkillWeighting(role_id=backend_role.id, skill_id=s_py.id, weight=1.0, is_core=True),
        RoleSkillWeighting(role_id=backend_role.id, skill_id=s_sql.id, weight=0.9, is_core=True),
        RoleSkillWeighting(role_id=backend_role.id, skill_id=s_dock.id, weight=0.8, is_core=False),
        RoleSkillWeighting(role_id=ds_role.id, skill_id=s_py.id, weight=1.0, is_core=True),
        RoleSkillWeighting(role_id=ds_role.id, skill_id=s_pd.id, weight=0.9, is_core=True),
        RoleSkillWeighting(role_id=ds_role.id, skill_id=s_torch.id, weight=0.8, is_core=False),
    ]
    db_session.add_all(weights)
    db_session.commit()
    return {"backend": backend_role, "data_science": ds_role}


class TestRecommendationService:
    def test_recommend_for_skills_ranking(
        self, db_session: Session, seeded_roles_and_skills: dict[str, TargetRole]
    ):
        # Candidate has Python and Docker -> Should rank Backend Developer higher than Data Scientist
        recs = recommendation_service.recommend_for_skills(
            db_session,
            skills=["Python", "Docker"],
            limit=5,
        )
        assert len(recs) == 2
        assert recs[0]["title"] == "Backend Developer"
        assert recs[0]["match_score"] > recs[1]["match_score"]
        assert "Docker" in recs[0]["matched_skills"]
        assert recs[1]["title"] == "Data Scientist"

    def test_recommend_with_category_filter(
        self, db_session: Session, seeded_roles_and_skills: dict[str, TargetRole]
    ):
        recs = recommendation_service.recommend_for_skills(
            db_session,
            skills=["Python", "Pandas"],
            category="Data & AI",
        )
        assert len(recs) == 1
        assert recs[0]["title"] == "Data Scientist"

    def test_recommend_for_user(
        self, db_session: Session, seeded_roles_and_skills: dict[str, TargetRole]
    ):
        user = User(email="ds_user@test.com", hashed_password="pw", full_name="DS User")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="Python")
        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="Pandas")
        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="PyTorch")

        recs = recommendation_service.recommend_for_user(
            db_session,
            user_id=user.id,
            limit=5,
        )
        assert len(recs) == 2
        assert recs[0]["title"] == "Data Scientist"
        assert recs[0]["match_score"] == 1.0
        assert recs[0]["coverage_pct"] == 100.0

    def test_recommend_for_text(
        self, db_session: Session, seeded_roles_and_skills: dict[str, TargetRole]
    ):
        text = "Skilled in Docker, PostgreSQL and Python backends with microservice architecture."
        result = recommendation_service.recommend_for_text(
            db_session,
            text=text,
            limit=3,
        )
        assert "extracted_skills" in result
        assert "recommendations" in result
        recs = result["recommendations"]
        assert len(recs) > 0
        assert recs[0]["title"] == "Backend Developer"
        assert recs[0]["match_score"] == 1.0
