"""Pydantic schemas for authentication and user credential handling."""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserRegisterRequest(BaseModel):
    """Payload for registering a new user account."""

    email: str = Field(..., description="Unique email address for account.")
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password (min 8 chars).")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name of user.")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not _EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email format.")
        return clean


class UserLoginRequest(BaseModel):
    """Payload for authenticating and obtaining an access token."""

    email: str = Field(..., description="Registered account email.")
    password: str = Field(..., min_length=1, description="Account password.")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not _EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email format.")
        return clean


class TokenResponse(BaseModel):
    """JWT bearer token response."""

    access_token: str = Field(..., description="Signed JWT bearer access token.")
    token_type: str = Field("bearer", description="Token type designation.")
    expires_in_seconds: int = Field(..., description="Validity duration in seconds.")
    user_id: int = Field(..., description="ID of the authenticated user.")
    email: str = Field(..., description="Email address of the authenticated user.")


class UserOut(BaseModel):
    """Public user profile DTO."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime] = None


class PasswordChangeRequest(BaseModel):
    """Payload for updating user password."""

    current_password: str = Field(..., min_length=1, description="Existing account password.")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password (min 8 chars).")
