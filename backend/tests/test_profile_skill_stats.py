"""Tests for the profile skill-stats endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient


class TestProfileSkillStatsEndpoint:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        email = f"skill_stats_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_skill_stats_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/profile/me/skill-stats")
        assert resp.status_code == 401

    def test_skill_stats_empty_profile(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        resp = client.get(
            "/api/v1/profile/me/skill-stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_skills"] == 0
        assert data["by_proficiency"] == {}
        assert data["by_category"] == {}

    def test_skill_stats_with_skills(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        suffix = uuid.uuid4().hex[:6]
        client.post("/api/v1/profile/me/skills", json={"skill_name": f"Python_{suffix}", "proficiency_level": "expert"}, headers=headers)
        client.post("/api/v1/profile/me/skills", json={"skill_name": f"Docker_{suffix}", "proficiency_level": "intermediate"}, headers=headers)

        resp = client.get("/api/v1/profile/me/skill-stats", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_skills"] == 2
        assert "expert" in data["by_proficiency"]
        assert "intermediate" in data["by_proficiency"]
