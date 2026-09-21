"""Integration tests for authenticated resume upload (/api/v1/resume/upload-to-my-profile)."""

from __future__ import annotations

import io
import uuid
import pytest
from starlette.testclient import TestClient

SAMPLE_RESUME_TXT = b"""Johnathan Coder
john.coder@example.com | 555-234-5678
https://github.com/johncoder

Summary
Experienced backend engineer building scalable web services.

Skills
Python, FastAPI, Docker, PostgreSQL, Redis

Experience
Software Engineer at Acme Corp (2021-Present)
- Developed REST APIs with FastAPI and PostgreSQL
- Deployed microservices using Docker
"""


class TestResumeAuthEndpoints:
    """Test suite for authenticated resume upload endpoint."""

    def _register_and_get_token(self, client: TestClient) -> tuple[str, str]:
        email = f"resume_user_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword123!"
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Resume Tester"},
        )
        assert reg_resp.status_code == 201

        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        return email, token

    def test_upload_to_my_profile_unauthenticated_returns_401(self, client: TestClient):
        files = {"file": ("resume.txt", io.BytesIO(SAMPLE_RESUME_TXT), "text/plain")}
        resp = client.post("/api/v1/resume/upload-to-my-profile", files=files)
        assert resp.status_code == 401

    def test_upload_to_my_profile_authenticated_success(self, client: TestClient):
        email, token = self._register_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        files = {"file": ("my_resume.txt", io.BytesIO(SAMPLE_RESUME_TXT), "text/plain")}

        resp = client.post(
            "/api/v1/resume/upload-to-my-profile",
            headers=headers,
            files=files,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "my_resume.txt"
        assert len(data["skills_raw"]) >= 2
        assert data["skills_matched"] >= 1
        assert data["profile_updated"] is True

        # Confirm the authenticated profile was actually updated
        me_resp = client.get("/api/v1/profile/me", headers=headers)
        assert me_resp.status_code == 200
        me_data = me_resp.json()["data"]
        assert len(me_data["skills"]) >= 2

