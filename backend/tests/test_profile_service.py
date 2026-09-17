"""Unit tests for ProfileService."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.role import TargetRole, UserTargetRole
from app.models.skill import Skill
from app.models.user import User
from app.services.profile_service import profile_service
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
def test_user(db_session: Session) -> User:
    user = User(
        email="dev_bob@example.com",
        hashed_password="hashed_pw_here",
        full_name="Bob Builder",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestProfileService:
    def test_upsert_profile_creates_new(self, db_session: Session, test_user: User):
        profile = profile_service.upsert_profile(
            db_session,
            user_id=test_user.id,
            headline="Senior Backend Engineer",
            bio="Building distributed systems.",
            current_title="Software Engineer",
            years_of_experience=5.5,
            location="Berlin, Germany",
            github_url="https://github.com/bob",
        )
        assert profile.user_id == test_user.id
        assert profile.headline == "Senior Backend Engineer"
        assert profile.years_of_experience == 5.5
        assert profile.location == "Berlin, Germany"
        assert profile.github_url == "https://github.com/bob"

    def test_upsert_profile_updates_existing(self, db_session: Session, test_user: User):
        profile_service.upsert_profile(
            db_session,
            user_id=test_user.id,
            headline="Junior Dev",
            years_of_experience=1.0,
        )
        updated = profile_service.upsert_profile(
            db_session,
            user_id=test_user.id,
            headline="Mid Dev",
            years_of_experience=2.5,
            bio="Upgraded bio",
        )
        assert updated.headline == "Mid Dev"
        assert updated.years_of_experience == 2.5
        assert updated.bio == "Upgraded bio"

    def test_upsert_nonexistent_user_raises(self, db_session: Session):
        with pytest.raises(ValueError, match="User with ID 999 not found"):
            profile_service.upsert_profile(db_session, user_id=999, headline="Ghost")

    def test_get_by_user_id(self, db_session: Session, test_user: User):
        assert profile_service.get_by_user_id(db_session, test_user.id) is None
        profile_service.upsert_profile(db_session, user_id=test_user.id, headline="Test")
        p = profile_service.get_by_user_id(db_session, test_user.id)
        assert p is not None
        assert p.headline == "Test"

    def test_get_full_profile(self, db_session: Session, test_user: User):
        # 1. Upsert profile
        profile_service.upsert_profile(
            db_session,
            user_id=test_user.id,
            headline="Cloud Architect",
            years_of_experience=8.0,
        )
        # 2. Add skill
        user_skill_service.add_user_skill(
            db_session,
            user_id=test_user.id,
            skill_name="Kubernetes",
            proficiency_level="expert",
        )
        # 3. Add target role
        role = TargetRole(
            title="Principal Engineer",
            slug="principal-engineer",
            category="Software Engineering",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserTargetRole(
            user_id=test_user.id,
            role_id=role.id,
            readiness_score=0.85,
        )
        db_session.add(user_role)
        db_session.commit()

        full = profile_service.get_full_profile(db_session, test_user.id)
        assert full is not None
        assert full["user_id"] == test_user.id
        assert full["email"] == "dev_bob@example.com"
        assert full["profile"]["headline"] == "Cloud Architect"
        assert len(full["skills"]) == 1
        assert full["skills"][0]["name"] == "Kubernetes"
        assert len(full["target_roles"]) == 1
        assert full["target_roles"][0]["title"] == "Principal Engineer"

    def test_get_full_profile_nonexistent(self, db_session: Session):
        assert profile_service.get_full_profile(db_session, 999) is None
