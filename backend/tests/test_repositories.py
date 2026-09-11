"""Unit tests for the generic and specialized repository pattern classes."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.job import JobPosting
from app.models.role import TargetRole
from app.models.skill import Skill, SkillCategory
from app.models.user import User
from app.repositories import (
    BaseRepository,
    job_repository,
    role_repository,
    skill_repository,
    user_repository,
)


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


class TestBaseRepository:
    """Test suite for generic BaseRepository operations."""

    def test_crud_lifecycle(self, db_session: Session) -> None:
        repo = BaseRepository(Skill)

        # 1. Create
        skill = repo.create(
            db_session,
            obj_in={"name": "Rust", "normalized_name": "rust", "category": "language"},
        )
        assert skill.id is not None
        assert skill.name == "Rust"

        # 2. Count & Get
        assert repo.count(db_session) == 1
        fetched = repo.get(db_session, skill.id)
        assert fetched is not None
        assert fetched.name == "Rust"

        # 3. Update
        updated = repo.update(
            db_session,
            db_obj=fetched,
            obj_in={"description": "Systems programming language"},
        )
        assert updated.description == "Systems programming language"

        # 4. Get Multi
        skills = repo.get_multi(db_session, skip=0, limit=10)
        assert len(skills) == 1

        # 5. Remove
        removed = repo.remove(db_session, entity_id=skill.id)
        assert removed is not None
        assert repo.count(db_session) == 0


class TestUserRepository:
    """Test suite for UserRepository specialized methods."""

    def test_get_by_email(self, db_session: Session) -> None:
        user = user_repository.create(
            db_session,
            obj_in={"email": "sam@example.com", "hashed_password": "pw", "full_name": "Sam"},
        )
        found = user_repository.get_by_email(db_session, email="sam@example.com")
        assert found is not None
        assert found.id == user.id

        not_found = user_repository.get_by_email(db_session, email="missing@example.com")
        assert not_found is None

    def test_get_active_users(self, db_session: Session) -> None:
        user_repository.create(
            db_session,
            obj_in={"email": "active@example.com", "hashed_password": "pw", "is_active": True},
        )
        user_repository.create(
            db_session,
            obj_in={"email": "inactive@example.com", "hashed_password": "pw", "is_active": False},
        )
        active = user_repository.get_active_users(db_session)
        assert len(active) == 1
        assert active[0].email == "active@example.com"


class TestJobRepository:
    """Test suite for JobRepository specialized methods."""

    def test_get_active_jobs_and_remote_filter(self, db_session: Session) -> None:
        job_repository.create(
            db_session,
            obj_in={
                "title": "Remote Go Engineer",
                "company_name": "CloudGo",
                "description": "desc",
                "is_remote": True,
                "is_active": True,
            },
        )
        job_repository.create(
            db_session,
            obj_in={
                "title": "Onsite Java Engineer",
                "company_name": "LegacyCo",
                "description": "desc",
                "is_remote": False,
                "is_active": True,
            },
        )

        remote_jobs = job_repository.get_active_jobs(db_session, is_remote=True)
        assert len(remote_jobs) == 1
        assert remote_jobs[0].title == "Remote Go Engineer"

        by_co = job_repository.get_by_company(db_session, company_name="CloudGo")
        assert len(by_co) == 1


class TestSkillRepository:
    """Test suite for SkillRepository specialized methods."""

    def test_skill_queries(self, db_session: Session) -> None:
        skill_repository.create(
            db_session,
            obj_in={"name": "Kubernetes", "normalized_name": "kubernetes", "category": "cloud_devops"},
        )
        by_name = skill_repository.get_by_name(db_session, name="Kubernetes")
        assert by_name is not None

        by_norm = skill_repository.get_by_normalized_name(db_session, normalized_name="kubernetes")
        assert by_norm is not None

        cloud_skills = skill_repository.get_by_category(db_session, category="cloud_devops")
        assert len(cloud_skills) == 1


class TestRoleRepository:
    """Test suite for RoleRepository specialized methods."""

    def test_role_queries(self, db_session: Session) -> None:
        role_repository.create(
            db_session,
            obj_in={
                "title": "Solutions Architect",
                "slug": "solutions-architect",
                "category": "Architecture",
                "is_active": True,
            },
        )
        by_slug = role_repository.get_by_slug(db_session, slug="solutions-architect")
        assert by_slug is not None
        assert by_slug.title == "Solutions Architect"

        roles = role_repository.get_active_roles(db_session, category="Architecture")
        assert len(roles) == 1
