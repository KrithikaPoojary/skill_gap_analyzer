"""Unit tests for authentication dependencies in app.api.deps."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import (
    get_current_active_user,
    get_current_superuser,
    get_current_user,
)
from app.core.security import create_access_token
from app.db.base import Base
from app.models.user import User


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
def active_user(db_session: Session) -> User:
    user = User(
        email="active@example.com",
        hashed_password="hash",
        full_name="Active User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def super_user(db_session: Session) -> User:
    user = User(
        email="admin@example.com",
        hashed_password="hash",
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestAuthDependencies:
    """Test suite for get_current_user and authorization guards."""

    def test_get_current_user_no_token_raises_401(self, db_session: Session):
        with pytest.raises(HTTPException) as exc:
            get_current_user(token=None, db=db_session)
        assert exc.value.status_code == 401
        assert "not provided" in exc.value.detail

    def test_get_current_user_invalid_token_raises_401(self, db_session: Session):
        with pytest.raises(HTTPException) as exc:
            get_current_user(token="invalid.garbage.token", db=db_session)
        assert exc.value.status_code == 401

    def test_get_current_user_valid_token_success(self, db_session: Session, active_user: User):
        token = create_access_token(subject=active_user.id)
        current = get_current_user(token=token, db=db_session)
        assert current.id == active_user.id
        assert current.email == active_user.email

    def test_get_current_user_nonexistent_subject_raises_401(self, db_session: Session):
        token = create_access_token(subject=99999)
        with pytest.raises(HTTPException) as exc:
            get_current_user(token=token, db=db_session)
        assert exc.value.status_code == 401
        assert "not found" in exc.value.detail

    def test_get_current_active_user_success(self, active_user: User):
        assert get_current_active_user(active_user).id == active_user.id

    def test_get_current_active_user_inactive_raises_403(self, active_user: User):
        active_user.is_active = False
        with pytest.raises(HTTPException) as exc:
            get_current_active_user(active_user)
        assert exc.value.status_code == 403
        assert "inactive" in exc.value.detail

    def test_get_current_superuser_success(self, super_user: User):
        assert get_current_superuser(super_user).id == super_user.id

    def test_get_current_superuser_forbidden_for_normal_user(self, active_user: User):
        with pytest.raises(HTTPException) as exc:
            get_current_superuser(active_user)
        assert exc.value.status_code == 403
        assert "administrator" in exc.value.detail
