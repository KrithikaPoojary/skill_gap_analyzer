"""Unit tests for app.schemas.auth (Pydantic validation schemas)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    PasswordChangeRequest,
    TokenResponse,
    UserLoginRequest,
    UserOut,
    UserRegisterRequest,
)


class TestAuthSchemas:
    """Test suite for authentication schemas."""

    def test_register_schema_valid(self):
        req = UserRegisterRequest(
            email="candidate@example.com",
            password="StrongPassword123!",
            full_name="Jane Doe",
        )
        assert req.email == "candidate@example.com"
        assert req.password == "StrongPassword123!"
        assert req.full_name == "Jane Doe"

    def test_register_schema_short_password(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="candidate@example.com",
                password="short",
            )

    def test_register_schema_invalid_email(self):
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                email="not-an-email",
                password="StrongPassword123!",
            )

    def test_login_schema_valid(self):
        req = UserLoginRequest(
            email="candidate@example.com",
            password="Password123!",
        )
        assert req.email == "candidate@example.com"
        assert req.password == "Password123!"

    def test_token_response_schema(self):
        res = TokenResponse(
            access_token="jwt.token.here",
            token_type="bearer",
            expires_in_seconds=3600,
            user_id=1,
            email="test@example.com",
        )
        assert res.access_token == "jwt.token.here"
        assert res.user_id == 1
        assert res.token_type == "bearer"

    def test_user_out_schema(self):
        user_data = {
            "id": 10,
            "email": "dev@example.com",
            "full_name": "Dev User",
            "is_active": True,
            "is_superuser": False,
        }
        out = UserOut.model_validate(user_data)
        assert out.id == 10
        assert out.email == "dev@example.com"
        assert out.is_active is True

    def test_password_change_schema_valid(self):
        req = PasswordChangeRequest(
            current_password="OldPassword123!",
            new_password="NewSecurePassword456!",
        )
        assert req.current_password == "OldPassword123!"
        assert req.new_password == "NewSecurePassword456!"

    def test_password_change_short_new_password(self):
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password="OldPassword123!",
                new_password="abc",
            )
