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
    ForgotPasswordRequest,
    PasswordChangeRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLoginRequest,
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


@router.delete(
    "/me",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Deactivate authenticated user's account",
    description="Mark the current user's account as inactive.",
)
def deactivate_me(
    current_user: CurrentActiveUser,
    db: DbSession,
) -> dict:
    """Deactivate account for the current user."""
    auth_service.deactivate_account(db, current_user)
    return {"message": "Account deactivated successfully."}


@router.delete(
    "/me/permanent",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Permanently delete current user's account",
    description="Completely delete the authenticated user's account and all cascaded data.",
)
def delete_me_permanently(
    current_user: CurrentActiveUser,
    db: DbSession,
) -> dict:
    """Permanently delete authenticated user account."""
    auth_service.hard_delete_account(db, current_user)
    return {"message": "Account permanently deleted."}


@router.post(
    "/reactivate",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Reactivate a deactivated account",
    description="Reactivate an inactive user account using valid credentials and issue a new JWT access token.",
)
def reactivate_account(
    req: UserLoginRequest,
    db: DbSession,
) -> TokenResponse:
    """Reactivate account and return auth token."""
    try:
        user = auth_service.reactivate_account(db, email=req.email, password=req.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return auth_service.create_token_response(user)


@router.post(
    "/forgot-password",

    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Request a password reset link",
    description="Generate a secure temporary password reset token for account recovery.",
)
def forgot_password(
    req: ForgotPasswordRequest,
    db: DbSession,
) -> dict:
    """Generate a password reset token for the requested email address."""
    token = auth_service.request_password_reset(db, email=req.email)
    return {
        "message": "If the account exists, a password reset token has been issued.",
        "reset_token": token,
    }


@router.post(
    "/reset-password",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Reset password using reset token",
    description="Validate password reset token and update account password.",
)
def reset_password(
    req: ResetPasswordRequest,
    db: DbSession,
) -> dict:
    """Validate reset token and set a new password."""
    try:
        auth_service.reset_password_with_token(
            db, token=req.token, new_password=req.new_password
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return {"message": "Password has been successfully reset. You can now log in."}

