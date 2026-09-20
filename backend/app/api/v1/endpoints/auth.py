"""Authentication REST API endpoints.

Provides:
  - POST /auth/register     – Create a new user account
  - POST /auth/login        – Authenticate and receive JWT token
  - GET  /auth/me           – Return the authenticated user's profile
  - POST /auth/change-password – Update the authenticated user's password
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends

from app.api.deps import CurrentActiveUser, DbSession
from app.schemas.auth import (
    PasswordChangeRequest,
    TokenResponse,
    UserOut,
    UserRegisterRequest,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Create a new candidate account and auto-provision an empty professional profile.",
)
def register_user(
    req: UserRegisterRequest,
    db: DbSession,
) -> UserOut:
    """Register a new user account with email and password."""
    try:
        user = auth_service.register_user(db, req)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return UserOut.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT token",
    description=(
        "Validate user credentials and issue a signed JWT bearer token. "
        "Compatible with OAuth2 password flow (`application/x-www-form-urlencoded`)."
    ),
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenResponse:
    """Authenticate user and return an access token."""
    user = auth_service.authenticate(
        db,
        email=form_data.username,
        password=form_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.create_token_response(user)


@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated user's public profile",
    description="Return the public profile of the currently authenticated user.",
)
def get_me(current_user: CurrentActiveUser) -> UserOut:
    """Return the authenticated user's account details."""
    return UserOut.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Change authenticated user's password",
    description="Update the current user's password given the correct existing credential.",
)
def change_password(
    req: PasswordChangeRequest,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> dict:
    """Update password for the authenticated user."""
    try:
        auth_service.change_password(db, current_user, req)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"message": "Password updated successfully."}
