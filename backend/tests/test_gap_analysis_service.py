"""Unit tests for GapAnalysisService."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.role import RoleSkillWeighting, TargetRole, UserTargetRole
from app.models.skill import Skill
from app.models.user import User
from app.services.gap_analysis_service import gap_analysis_service
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
def seeded_role(db_session: Session) -> TargetRole:
    """Seed a target role with benchmark skills."""
    role = TargetRole(
        title="Backend Engineer",
        slug="backend-engineer",
        category="Software Engineering",
        min_experience_years=2.0,
    )
    db_session.add(role)
    db_session.flush()

    skills = [
        Skill(name="Python", normalized_name="python", category="language"),
        Skill(name="PostgreSQL", normalized_name="postgresql", category="database"),
        Skill(name="Docker", normalized_name="docker", category="cloud_devops"),
        Skill(name="Kubernetes", normalized_name="kubernetes", category="cloud_devops"),
    ]
    db_session.add_all(skills)
    db_session.flush()

    weights = [
        RoleSkillWeighting(role_id=role.id, skill_id=skills[0].id, weight=1.0, is_core=True),
        RoleSkillWeighting(role_id=role.id, skill_id=skills[1].id, weight=0.9, is_core=True),
        RoleSkillWeighting(role_id=role.id, skill_id=skills[2].id, weight=0.7, is_core=False),
        RoleSkillWeighting(role_id=role.id, skill_id=skills[3].id, weight=0.5, is_core=False),
    ]
    db_session.add_all(weights)
    db_session.commit()
    db_session.refresh(role)
    return role


class TestGapAnalysisService:
    def test_find_target_role_by_id(self, db_session: Session, seeded_role: TargetRole):
        found = gap_analysis_service.find_target_role(db_session, role_id=seeded_role.id)
        assert found is not None
        assert found.id == seeded_role.id

    def test_find_target_role_by_slug(self, db_session: Session, seeded_role: TargetRole):
        found = gap_analysis_service.find_target_role(db_session, role_slug="backend-engineer")
        assert found is not None
        assert found.title == "Backend Engineer"

    def test_find_target_role_by_name(self, db_session: Session, seeded_role: TargetRole):
        found = gap_analysis_service.find_target_role(db_session, role_name="Backend Engineer")
        assert found is not None
        assert found.id == seeded_role.id

    def test_analyse_skills_partial_match(self, db_session: Session, seeded_role: TargetRole):
        # Candidate has Python and Docker
        report = gap_analysis_service.analyse_skills(
            db_session,
            profile_skills=["Python", "Docker", "Git"],
            role_id=seeded_role.id,
        )
        assert report["role_name"] == "Backend Engineer"
        assert set(report["matched_skills"]) == {"Python", "Docker"}
        assert "PostgreSQL" in [s["name"] for s in report["missing_skills"]]
        assert "Git" in report["surplus_skills"]
        assert report["coverage_pct"] == 50.0  # 2 of 4
        assert 0.0 < report["weighted_gap_score"] < 1.0

    def test_analyse_from_text(self, db_session: Session, seeded_role: TargetRole):
        text = "Experienced developer proficient in Python and PostgreSQL with some AWS skills."
        result = gap_analysis_service.analyse_from_text(
            db_session,
            text=text,
            role_id=seeded_role.id,
        )
        assert "extracted_skills" in result
        assert "gap_report" in result
        gap_rep = result["gap_report"]
        assert "Python" in gap_rep["matched_skills"]
        assert "PostgreSQL" in gap_rep["matched_skills"]

    def test_analyse_for_user(self, db_session: Session, seeded_role: TargetRole):
        user = User(
            email="candidate@test.com",
            hashed_password="pw",
            full_name="Test Candidate",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="Python")
        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="PostgreSQL")
        user_skill_service.add_user_skill(db_session, user_id=user.id, skill_name="Docker")

        report = gap_analysis_service.analyse_for_user(
            db_session,
            user_id=user.id,
            role_slug="backend-engineer",
        )
        assert len(report["matched_skills"]) == 3
        assert report["weighted_gap_score"] > 0.8

        # Check readiness score saved to UserTargetRole
        utr = db_session.query(UserTargetRole).filter_by(user_id=user.id, role_id=seeded_role.id).first()
        assert utr is not None
        assert utr.readiness_score == report["weighted_gap_score"]
