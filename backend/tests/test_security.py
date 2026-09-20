"""Unit tests for app.core.security (password hashing & JWT handling)."""

from __future__ import annotations

from datetime import timedelta
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Test suite for bcrypt password hashing and verification."""

    def test_hash_password_produces_bcrypt_hash(self):
        pwd = "SecurePassword123!"
        hashed = hash_password(pwd)
        assert hashed != pwd
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_password_success(self):
        pwd = "MySecretPassword"
        hashed = hash_password(pwd)
        assert verify_password(pwd, hashed) is True

    def test_verify_password_mismatch(self):
        pwd = "CorrectPassword"
        hashed = hash_password(pwd)
        assert verify_password("WrongPassword", hashed) is False

    def test_verify_password_invalid_hash(self):
        assert verify_password("Password", "not-a-bcrypt-hash") is False
        assert verify_password("", "") is False
        assert verify_password("Password", "") is False

    def test_hash_empty_password_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            hash_password("")


class TestJwtTokens:
    """Test suite for JWT token creation, encoding, decoding, and expiration."""

    def test_create_and_decode_token(self):
        user_id = 42
        token = create_access_token(subject=user_id)
        payload = decode_access_token(token)

        assert payload["sub"] == "42"
        assert "exp" in payload
        assert "iat" in payload

    def test_token_with_extra_claims(self):
        token = create_access_token(
            subject=10,
            extra_claims={"email": "alice@example.com", "role": "admin"},
        )
        payload = decode_access_token(token)

        assert payload["sub"] == "10"
        assert payload["email"] == "alice@example.com"
        assert payload["role"] == "admin"

    def test_expired_token_raises_value_error(self):
        expired_token = create_access_token(
            subject=1,
            expires_delta=timedelta(seconds=-10),
        )
        with pytest.raises(ValueError, match="Token has expired"):
            decode_access_token(expired_token)

    def test_invalid_token_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid authentication token"):
            decode_access_token("invalid.token.signature")
