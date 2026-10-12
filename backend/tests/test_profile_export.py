"""Tests for the profile data export endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient


class TestProfileExportEndpoint:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        email = f"export_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_export_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/profile/me/export")
        assert resp.status_code == 401

    def test_export_authenticated_user_profile(self, client: TestClient) -> None:
        uid, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Add profile details
        client.put(
            "/api/v1/profile/me",
            json={"headline": "Software Engineer", "years_of_experience": 4.5, "location": "Bengaluru"},
            headers=headers,
        )

        # Add a skill
        suffix = uuid.uuid4().hex[:6]
        client.post(
            "/api/v1/profile/me/skills",
            json={"skill_name": f"Golang_{suffix}", "proficiency_level": "intermediate", "years_of_experience": 2.0},
            headers=headers,
        )

        resp = client.get("/api/v1/profile/me/export", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]

        assert "exported_at" in data
        assert data["user"]["id"] == uid
        assert data["profile"]["headline"] == "Software Engineer"
        assert len(data["skills"]) >= 1
        skill_names = [s["name"] for s in data["skills"]]
        assert f"Golang_{suffix}" in skill_names
        assert isinstance(data["target_roles"], list)
