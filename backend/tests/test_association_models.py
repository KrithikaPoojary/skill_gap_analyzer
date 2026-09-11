"""Unit tests for JobSkill and UserSkill many-to-many association models."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.associations import JobSkill, UserSkill
from app.models.job import JobPosting
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


class TestJobSkillAssociation:
    """Test suite for JobPosting to Skill association."""

    def test_associate_job_with_skills(self, db_session: Session) -> None:
        job = JobPosting(
            title="Full Stack Engineer",
            company_name="CloudNine",
            description="Full stack engineering role",
        )
        skill_python = Skill(
            name="Python",
            normalized_name="python",
            category=SkillCategory.LANGUAGE.value,
        )
        skill_react = Skill(
            name="React",
            normalized_name="react",
            category=SkillCategory.FRAMEWORK.value,
        )
        db_session.add_all([job, skill_python, skill_react])
        db_session.commit()

        # Add JobSkills
        js_python = JobSkill(
            job=job,
            skill=skill_python,
            is_required=True,
            importance_weight=5.0,
        )
        js_react = JobSkill(
            job=job,
            skill=skill_react,
            is_required=False,
            importance_weight=3.0,
        )
        db_session.add_all([js_python, js_react])
        db_session.commit()

        db_session.refresh(job)
        assert len(job.job_skills) == 2
        skills_in_job = {js.skill.name: js.is_required for js in job.job_skills}
        assert skills_in_job["Python"] is True
        assert skills_in_job["React"] is False
        assert repr(js_python).startswith("<JobSkill")

    def test_cascade_delete_job_removes_associations_preserves_skill(
        self, db_session: Session
    ) -> None:
        job = JobPosting(title="DevOps Engineer", company_name="InfraCorp", description="desc")
        skill = Skill(name="Terraform", normalized_name="terraform", category=SkillCategory.CLOUD_DEVOPS.value)
        db_session.add_all([job, skill])
        db_session.commit()

        js = JobSkill(job=job, skill=skill)
        db_session.add(js)
        db_session.commit()

        job_id = job.id
        skill_id = skill.id

        # Delete job
        db_session.delete(job)
        db_session.commit()

        # Association is deleted
        assert db_session.query(JobSkill).filter_by(job_id=job_id).first() is None
        # Skill is preserved
        assert db_session.query(Skill).filter_by(id=skill_id).first() is not None


class TestUserSkillAssociation:
    """Test suite for User to Skill association."""

    def test_associate_user_with_skills(self, db_session: Session) -> None:
        user = User(email="learner@example.com", hashed_password="pw")
        skill = Skill(name="Docker", normalized_name="docker", category=SkillCategory.CLOUD_DEVOPS.value)
        db_session.add_all([user, skill])
        db_session.commit()

        user_skill = UserSkill(
            user=user,
            skill=skill,
            proficiency_level="advanced",
            years_of_experience=3.5,
            is_verified=True,
        )
        db_session.add(user_skill)
        db_session.commit()

        db_session.refresh(user)
        assert len(user.user_skills) == 1
        us = user.user_skills[0]
        assert us.skill.name == "Docker"
        assert us.proficiency_level == "advanced"
        assert us.years_of_experience == 3.5
        assert us.is_verified is True
        assert repr(user_skill).startswith("<UserSkill")
