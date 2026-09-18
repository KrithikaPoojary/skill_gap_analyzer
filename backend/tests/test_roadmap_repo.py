"""Unit tests for RoadmapRepository."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import User
from app.repositories.roadmap_repo import roadmap_repository


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
def sample_user(db_session: Session) -> User:
    user = User(email="repo_tester@example.com", hashed_password="pw", full_name="Repo User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestRoadmapRepository:
    def test_create_roadmap_with_phases(self, db_session: Session, sample_user: User):
        phases_data = [
            {
                "phase_number": 1,
                "phase_title": "Foundations",
                "description": "Learn basic Python",
                "capstone_project_title": "CLI Weather App",
                "capstone_project_description": "Build CLI app in Python",
                "total_phase_hours": 30,
                "estimated_weeks": 3,
                "skills": [
                    {"name": "Python", "estimated_hours": 30, "difficulty": "beginner"}
                ],
            },
            {
                "phase_number": 2,
                "phase_title": "Frameworks",
                "description": "Learn FastAPI & Docker",
                "capstone_project_title": "REST API Container",
                "total_phase_hours": 38,
                "estimated_weeks": 4,
                "skills": [
                    {"name": "FastAPI", "estimated_hours": 20, "difficulty": "intermediate"},
                    {"name": "Docker", "estimated_hours": 18, "difficulty": "intermediate"},
                ],
            },
        ]

        roadmap = roadmap_repository.create_roadmap_with_phases(
            db_session,
            user_id=sample_user.id,
            target_role_id=None,
            title="Backend Journey",
            target_role_name="Backend Engineer",
            total_skills=3,
            total_estimated_hours=68,
            weekly_commitment_hours=10,
            estimated_weeks=7,
            phases_data=phases_data,
        )

        assert roadmap.id is not None
        assert roadmap.title == "Backend Journey"
        assert len(roadmap.milestones) == 2
        assert len(roadmap.milestones[1].skills) == 2

        # Verify get_by_id_with_milestones
        fetched = roadmap_repository.get_by_id_with_milestones(db_session, roadmap.id)
        assert fetched is not None
        assert len(fetched.milestones) == 2
        assert fetched.milestones[0].phase_title == "Foundations"

    def test_get_user_roadmaps(self, db_session: Session, sample_user: User):
        roadmap_repository.create_roadmap_with_phases(
            db_session,
            user_id=sample_user.id,
            target_role_id=None,
            title="Roadmap A",
            target_role_name="Role A",
            total_skills=1,
            total_estimated_hours=20,
            weekly_commitment_hours=10,
            estimated_weeks=2,
            phases_data=[],
        )
        roadmaps = roadmap_repository.get_user_roadmaps(db_session, user_id=sample_user.id)
        assert len(roadmaps) == 1
        assert roadmaps[0].title == "Roadmap A"

    def test_update_milestone_completion(self, db_session: Session, sample_user: User):
        phases_data = [
            {
                "phase_number": 1,
                "phase_title": "P1",
                "skills": [{"name": "Git", "estimated_hours": 10}],
            }
        ]
        roadmap = roadmap_repository.create_roadmap_with_phases(
            db_session,
            user_id=sample_user.id,
            target_role_id=None,
            title="Single Milestone",
            target_role_name="Role B",
            total_skills=1,
            total_estimated_hours=10,
            weekly_commitment_hours=10,
            estimated_weeks=1,
            phases_data=phases_data,
        )

        milestone = roadmap.milestones[0]
        assert milestone.is_completed is False

        # Mark milestone completed
        updated = roadmap_repository.update_milestone_completion(
            db_session, milestone_id=milestone.id, is_completed=True
        )
        assert updated is not None
        assert updated.is_completed is True
        assert updated.skills[0].is_completed is True

        # Roadmap auto-completed
        refreshed_rm = roadmap_repository.get_by_id_with_milestones(db_session, roadmap.id)
        assert refreshed_rm.status == "completed"
