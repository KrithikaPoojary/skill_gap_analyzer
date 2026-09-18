"""Unit tests for LearningRoadmap, RoadmapMilestone, and MilestoneSkill ORM models."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.roadmap import LearningRoadmap, MilestoneSkill, RoadmapMilestone
from app.models.role import TargetRole
from app.models.skill import Skill
from app.models.user import User


@pytest.fixture
def db_session():
    """Temporary in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestRoadmapModels:
    def test_create_learning_roadmap_with_milestones_and_skills(self, db_session: Session):
        user = User(email="learner@example.com", hashed_password="pw", full_name="Learner One")
        db_session.add(user)
        db_session.flush()

        role = TargetRole(title="Cloud Architect", slug="cloud-architect")
        db_session.add(role)
        db_session.flush()

        skill_py = Skill(name="Python", normalized_name="python")
        skill_docker = Skill(name="Docker", normalized_name="docker")
        db_session.add_all([skill_py, skill_docker])
        db_session.flush()

        roadmap = LearningRoadmap(
            user_id=user.id,
            target_role_id=role.id,
            title="Cloud Architect Mastery Path",
            target_role_name="Cloud Architect",
            total_skills=2,
            total_estimated_hours=48,
            weekly_commitment_hours=12,
            estimated_weeks=4,
            status="active",
        )
        db_session.add(roadmap)
        db_session.flush()

        m1 = RoadmapMilestone(
            roadmap_id=roadmap.id,
            phase_number=1,
            phase_title="Core Foundations",
            description="Foundational scripting.",
            capstone_project_title="CLI Tool",
            order_index=0,
            total_phase_hours=30,
            estimated_weeks=3,
        )
        db_session.add(m1)
        db_session.flush()

        ms1 = MilestoneSkill(
            milestone_id=m1.id,
            skill_id=skill_py.id,
            skill_name="Python",
            estimated_hours=30,
            difficulty="beginner",
        )
        db_session.add(ms1)
        db_session.commit()

        # Query and verify relationships
        saved = db_session.get(LearningRoadmap, roadmap.id)
        assert saved is not None
        assert saved.user.email == "learner@example.com"
        assert saved.target_role.title == "Cloud Architect"
        assert len(saved.milestones) == 1
        assert saved.milestones[0].phase_title == "Core Foundations"
        assert len(saved.milestones[0].skills) == 1
        assert saved.milestones[0].skills[0].skill_name == "Python"
        assert saved.milestones[0].skills[0].is_completed is False

    def test_cascade_delete_roadmap_removes_milestones(self, db_session: Session):
        roadmap = LearningRoadmap(
            title="Temp Path",
            target_role_name="Tester",
            total_skills=1,
        )
        db_session.add(roadmap)
        db_session.flush()

        milestone = RoadmapMilestone(
            roadmap_id=roadmap.id,
            phase_number=1,
            phase_title="P1",
        )
        db_session.add(milestone)
        db_session.commit()

        m_id = milestone.id
        db_session.delete(roadmap)
        db_session.commit()

        assert db_session.get(RoadmapMilestone, m_id) is None
