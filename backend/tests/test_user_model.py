"""Unit tests for User and Profile SQLAlchemy ORM models."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import Profile, User


@pytest.fixture
def db_session():
    """Create a temporary in-memory database session for isolated model tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestUserModel:
    """Test suite for User model functionality."""

    def test_create_user(self, db_session: Session) -> None:
        user = User(
            email="developer@example.com",
            hashed_password="secure_hash_secret",
            full_name="Alex Mercer",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "developer@example.com"
        assert user.full_name == "Alex Mercer"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.created_at is not None
        assert user.updated_at is not None
        assert "developer@example.com" in repr(user)

    def test_unique_email_constraint(self, db_session: Session) -> None:
        user1 = User(email="duplicate@example.com", hashed_password="pw1")
        user2 = User(email="duplicate@example.com", hashed_password="pw2")
        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestProfileModel:
    """Test suite for Profile model and User-Profile relationship."""

    def test_create_user_with_profile(self, db_session: Session) -> None:
        user = User(email="pro@example.com", hashed_password="hashed_pw", full_name="Jane Doe")
        profile = Profile(
            user=user,
            headline="Senior Backend Engineer",
            bio="Passionate about distributed systems.",
            current_title="Software Architect",
            years_of_experience=7.5,
            location="Bangalore, India",
            github_url="https://github.com/janedoe",
            linkedin_url="https://linkedin.com/in/janedoe",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.profile is not None
        assert user.profile.headline == "Senior Backend Engineer"
        assert user.profile.years_of_experience == 7.5
        assert user.profile.user_id == user.id
        assert repr(user.profile).startswith("<Profile")

    def test_profile_cascade_deletion(self, db_session: Session) -> None:
        user = User(email="delete_me@example.com", hashed_password="pw")
        profile = Profile(user=user, headline="To be deleted")
        db_session.add(user)
        db_session.commit()

        user_id = user.id
        db_session.delete(user)
        db_session.commit()

        deleted_profile = db_session.query(Profile).filter_by(user_id=user_id).first()
        assert deleted_profile is None
