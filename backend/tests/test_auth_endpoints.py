"""Integration tests for authentication REST API endpoints."""

from __future__ import annotations

import uuid
import pytest
from starlette.testclient import TestClient


class TestAuthEndpoints:
    """Test suite for /api/v1/auth/* endpoints."""

    def test_register_user_success(self, client: TestClient):
        email = f"user_{uuid.uuid4().hex[:8]}@example.com"
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "SuperSecure123!",
                "full_name": "Test User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == email
        assert data["full_name"] == "Test User"
        assert data["is_active"] is True
        assert "id" in data

    def test_register_duplicate_email_returns_409(self, client: TestClient):
        email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"
        payload = {"email": email, "password": "SecurePass123!", "full_name": "First"}
        client.post("/api/v1/auth/register", json=payload)

        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409
        body = resp.json()
        # Response is in the standardized error envelope: {"error": {"message": "..."}}
        error_message = body.get("detail") or body.get("error", {}).get("message", "")
        assert "already exists" in error_message

    def test_register_invalid_password_returns_422(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": f"invalid_{uuid.uuid4().hex[:8]}@example.com", "password": "short"},
        )
        assert resp.status_code == 422

    def test_login_success(self, client: TestClient):
        email = f"login_{uuid.uuid4().hex[:8]}@example.com"
        password = "MyLoginPass123!"
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )

        resp = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] > 0

    def test_login_wrong_password_returns_401(self, client: TestClient):
        email = f"wrong_{uuid.uuid4().hex[:8]}@example.com"
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "CorrectPass123!"},
        )

        resp = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "WrongPassword!"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email_returns_401(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": f"ghost_{uuid.uuid4().hex[:8]}@example.com", "password": "anypassword"},
        )
        assert resp.status_code == 401

    def test_get_me_authenticated(self, client: TestClient):
        email = f"me_{uuid.uuid4().hex[:8]}@example.com"
        password = "MeEndpointPass123!"
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )

        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        token = login_resp.json()["access_token"]

        me_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email

    def test_get_me_unauthenticated_returns_401(self, client: TestClient):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_change_password_success(self, client: TestClient):
        email = f"changepw_{uuid.uuid4().hex[:8]}@example.com"
        old_pw = "OldPassword123!"
        new_pw = "NewSecurePass456!"
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": old_pw},
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": old_pw},
        )
        token = login_resp.json()["access_token"]

        resp = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": old_pw, "new_password": new_pw},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "updated successfully" in resp.json()["message"]

        # Confirm new password works
        new_login = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": new_pw},
        )
        assert new_login.status_code == 200

    def test_deactivate_account_success(self, client: TestClient):
        email = f"deact_{uuid.uuid4().hex[:8]}@example.com"
        password = "Password123!"
        client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        token = login_resp.json()["access_token"]

        resp = client.delete("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "deactivated" in resp.json()["message"]

        # Subsequent authenticated requests should fail with 400 inactive
        me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 400
