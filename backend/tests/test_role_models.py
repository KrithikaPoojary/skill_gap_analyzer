"""Unit tests for TargetRole, RoleSkillWeighting, and UserTargetRole ORM models."""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.role import RoleSkillWeighting, TargetRole, UserTargetRole
from app.models.skill import Skill, SkillCategory
from app.models.user import User


@pytest.fixture
def db_session():
    """Create a temporary in-memory database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestTargetRoleModel:
    """Test suite for TargetRole benchmark profile."""

    def test_create_target_role(self, db_session: Session) -> None:
        role = TargetRole(
            title="Backend Engineer",
            slug="backend-engineer",
            description="Designs and scales server-side systems and APIs.",
            category="Software Engineering",
            min_experience_years=2.0,
        )
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)

        assert role.id is not None
        assert role.title == "Backend Engineer"
        assert role.slug == "backend-engineer"
        assert role.min_experience_years == 2.0
        assert role.is_active is True
        assert repr(role).startswith("<TargetRole")

    def test_unique_slug_and_title(self, db_session: Session) -> None:
        r1 = TargetRole(title="DevOps", slug="devops")
        r2 = TargetRole(title="DevOps", slug="devops-2")
        db_session.add(r1)
        db_session.commit()

        db_session.add(r2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestRoleSkillWeighting:
    """Test suite for RoleSkillWeighting benchmark mapping."""

    def test_link_role_skills_with_weights(self, db_session: Session) -> None:
        role = TargetRole(title="Data Scientist", slug="data-scientist")
        skill_python = Skill(name="Python", normalized_name="python", category=SkillCategory.LANGUAGE.value)
        skill_pytorch = Skill(name="PyTorch", normalized_name="pytorch", category=SkillCategory.AI_ML.value)
        db_session.add_all([role, skill_python, skill_pytorch])
        db_session.commit()

        w_python = RoleSkillWeighting(
            role=role,
            skill=skill_python,
            weight=5.0,
            is_core=True,
            benchmark_level="advanced",
        )
        w_pytorch = RoleSkillWeighting(
            role=role,
            skill=skill_pytorch,
            weight=4.0,
            is_core=True,
            benchmark_level="intermediate",
        )
        db_session.add_all([w_python, w_pytorch])
        db_session.commit()

        db_session.refresh(role)
        assert len(role.role_skills) == 2
        core_skills = {rw.skill.name: rw.weight for rw in role.role_skills if rw.is_core}
        assert core_skills["Python"] == 5.0
        assert core_skills["PyTorch"] == 4.0
        assert repr(w_python).startswith("<RoleSkillWeighting")


class TestUserTargetRole:
    """Test suite for UserTargetRole aspirational career mapping."""

    def test_user_target_role_association(self, db_session: Session) -> None:
        user = User(email="aspirant@example.com", hashed_password="pw")
        role = TargetRole(title="Cloud Architect", slug="cloud-architect")
        db_session.add_all([user, role])
        db_session.commit()

        target_date = datetime.now(timezone.utc)
        user_role = UserTargetRole(
            user=user,
            role=role,
            target_date=target_date,
            readiness_score=68.5,
        )
        db_session.add(user_role)
        db_session.commit()

        db_session.refresh(user)
        assert len(user.target_roles) == 1
        assert user.target_roles[0].readiness_score == 68.5
        assert user.target_roles[0].role.slug == "cloud-architect"
        assert repr(user_role).startswith("<UserTargetRole")
