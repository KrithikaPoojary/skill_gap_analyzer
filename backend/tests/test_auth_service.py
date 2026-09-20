"""Unit tests for app.services.auth_service."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import verify_password
from app.db.base import Base
from app.models.user import Profile, User
from app.schemas.auth import (
    PasswordChangeRequest,
    UserRegisterRequest,
)
from app.services.auth_service import AuthService, auth_service


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


class TestAuthService:
    """Test suite for AuthService operations."""

    def test_register_user_creates_user_and_profile(self, db_session: Session):
        service = AuthService()
        req = UserRegisterRequest(
            email="newcandidate@example.com",
            password="SecurePassword999!",
            full_name="Candidate One",
        )
        user = service.register_user(db_session, req)

        assert user.id is not None
        assert user.email == "newcandidate@example.com"
        assert user.full_name == "Candidate One"
        assert verify_password("SecurePassword999!", user.hashed_password) is True

        # Verify auto-provisioned profile
        profile = db_session.query(Profile).filter_by(user_id=user.id).first()
        assert profile is not None
        assert profile.years_of_experience == 0.0

    def test_register_duplicate_email_raises_value_error(self, db_session: Session):
        service = AuthService()
        req = UserRegisterRequest(
            email="duplicate@example.com",
            password="SecurePassword999!",
        )
        service.register_user(db_session, req)

        with pytest.raises(ValueError, match="already exists"):
            service.register_user(db_session, req)

    def test_authenticate_success(self, db_session: Session):
        service = AuthService()
        req = UserRegisterRequest(
            email="auth_success@example.com",
            password="CorrectPassword123!",
        )
        registered = service.register_user(db_session, req)

        authenticated = service.authenticate(
            db_session,
            email="auth_success@example.com",
            password="CorrectPassword123!",
        )
        assert authenticated is not None
        assert authenticated.id == registered.id

    def test_authenticate_wrong_password(self, db_session: Session):
        service = AuthService()
        req = UserRegisterRequest(
            email="auth_fail@example.com",
            password="CorrectPassword123!",
        )
        service.register_user(db_session, req)

        authenticated = service.authenticate(
            db_session,
            email="auth_fail@example.com",
            password="WrongPassword456!",
        )
        assert authenticated is None

    def test_authenticate_nonexistent_email(self, db_session: Session):
        service = AuthService()
        authenticated = service.authenticate(
            db_session,
            email="ghost@example.com",
            password="SomePassword123!",
        )
        assert authenticated is None

    def test_authenticate_inactive_user(self, db_session: Session):
        service = AuthService()
        req = UserRegisterRequest(
            email="inactive@example.com",
            password="CorrectPassword123!",
        )
        user = service.register_user(db_session, req)
        user.is_active = False
        db_session.commit()

        authenticated = service.authenticate(
            db_session,
            email="inactive@example.com",
            password="CorrectPassword123!",
        )
        assert authenticated is None

    def test_create_token_response(self, db_session: Session):
        service = AuthService()
        req = UserRegisterRequest(
            email="tokentest@example.com",
            password="CorrectPassword123!",
        )
        user = service.register_user(db_session, req)
        token_resp = service.create_token_response(user)

        assert token_resp.access_token != ""
        assert token_resp.user_id == user.id
        assert token_resp.email == "tokentest@example.com"
        assert token_resp.expires_in_seconds > 0

    def test_change_password_success(self, db_session: Session):
        service = AuthService()
        req = UserRegisterRequest(
            email="change_pwd@example.com",
            password="OldPassword123!",
        )
        user = service.register_user(db_session, req)

        change_req = PasswordChangeRequest(
            current_password="OldPassword123!",
            new_password="BrandNewPassword789!",
        )
        result = service.change_password(db_session, user, change_req)
        assert result is True
        assert verify_password("BrandNewPassword789!", user.hashed_password) is True

    def test_change_password_wrong_current(self, db_session: Session):
        service = AuthService()
        req = UserRegisterRequest(
            email="change_wrong@example.com",
            password="OldPassword123!",
        )
        user = service.register_user(db_session, req)

        change_req = PasswordChangeRequest(
            current_password="IncorrectCurrentPassword!",
            new_password="BrandNewPassword789!",
        )
        with pytest.raises(ValueError, match="Current password is incorrect"):
            service.change_password(db_session, user, change_req)
