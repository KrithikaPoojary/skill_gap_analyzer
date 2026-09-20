"""Authentication and user account domain service."""

from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import Profile, User
from app.repositories.user_repo import UserRepository, user_repository
from app.schemas.auth import (
    PasswordChangeRequest,
    TokenResponse,
    UserRegisterRequest,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Handles credential authentication, registration, password lifecycle, and JWT issuance."""

    def __init__(self, user_repo: UserRepository | None = None) -> None:
        self._user_repo = user_repo or user_repository

    def register_user(self, db: Session, req: UserRegisterRequest) -> User:
        """Register a new candidate account and auto-provision an empty profile.

        Raises:
            ValueError: If the email address is already taken.
        """
        existing = self._user_repo.get_by_email(db, email=req.email)
        if existing:
            raise ValueError(f"Account with email '{req.email}' already exists.")

        hashed_pwd = hash_password(req.password)
        user = User(
            email=req.email.strip().lower(),
            hashed_password=hashed_pwd,
            full_name=req.full_name.strip() if req.full_name else None,
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.flush()

        # Provision profile record linked to user
        profile = Profile(
            user_id=user.id,
            years_of_experience=0.0,
        )
        db.add(profile)
        db.commit()
        db.refresh(user)

        logger.info("Registered new user '%s' (id=%d).", user.email, user.id)
        return user

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        """Verify user credentials and return User entity if valid."""
        user = self._user_repo.get_by_email(db, email=email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_token_response(self, user: User) -> TokenResponse:
        """Issue a signed JWT access token response for an authenticated user."""
        token = create_access_token(
            subject=user.id,
            extra_claims={
                "email": user.email,
                "is_superuser": user.is_superuser,
            },
        )
        expires_seconds = settings.access_token_expire_minutes * 60
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_seconds=expires_seconds,
            user_id=user.id,
            email=user.email,
        )

    def change_password(self, db: Session, user: User, req: PasswordChangeRequest) -> bool:
        """Update password for an authenticated user.

        Raises:
            ValueError: If current password does not match.
        """
        if not verify_password(req.current_password, user.hashed_password):
            raise ValueError("Current password is incorrect.")

        user.hashed_password = hash_password(req.new_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Password updated for user id=%d.", user.id)
        return True


# Module-level singleton
auth_service = AuthService()
