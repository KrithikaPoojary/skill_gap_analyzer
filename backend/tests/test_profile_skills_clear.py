"""Tests for clearing all user skills on candidate profile."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient


class TestProfileSkillsClear:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"prof_clear_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_clear_all_skills(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Add two skills
        client.post(
            "/api/v1/profile/me/skills",
            json={"skill_name": f"SkillA_{uuid.uuid4().hex[:6]}", "proficiency_level": "beginner"},
            headers=headers,
        )
        client.post(
            "/api/v1/profile/me/skills",
            json={"skill_name": f"SkillB_{uuid.uuid4().hex[:6]}", "proficiency_level": "intermediate"},
            headers=headers,
        )

        # Verify skills are present
        skills_resp = client.get("/api/v1/profile/me/skills", headers=headers)
        assert skills_resp.status_code == 200
        assert skills_resp.json()["data"]["total"] == 2

        # Clear all skills
        clear_resp = client.delete("/api/v1/profile/me/skills", headers=headers)
        assert clear_resp.status_code == 200
        assert clear_resp.json()["data"]["cleared_count"] == 2

        # Verify empty profile skills list
        empty_skills = client.get("/api/v1/profile/me/skills", headers=headers)
        assert empty_skills.status_code == 200
        assert empty_skills.json()["data"]["total"] == 0

    def test_clear_empty_skills(self, client: TestClient) -> None:
        _, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        clear_resp = client.delete("/api/v1/profile/me/skills", headers=headers)
        assert clear_resp.status_code == 200
        assert clear_resp.json()["data"]["cleared_count"] == 0
