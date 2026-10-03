"""Tests for updating user profile skill proficiency."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient


class TestProfileSkillUpdate:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"prof_skill_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_update_skill_proficiency_and_experience(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Add a skill first
        add_resp = client.post(
            "/api/v1/profile/me/skills",
            json={
                "skill_name": f"Docker_{uuid.uuid4().hex[:6]}",
                "proficiency_level": "beginner",
                "years_of_experience": 0.5,
            },
            headers=headers,
        )
        assert add_resp.status_code in (200, 201)
        skill_id = add_resp.json()["data"]["skill_id"]

        # Update proficiency and experience
        patch_resp = client.patch(
            f"/api/v1/profile/me/skills/{skill_id}",
            json={
                "proficiency_level": "expert",
                "years_of_experience": 4.5,
            },
            headers=headers,
        )
        assert patch_resp.status_code == 200
        data = patch_resp.json()["data"]
        assert data["skill_id"] == skill_id
        assert data["proficiency_level"] == "expert"
        assert data["years_of_experience"] == 4.5

    def test_update_non_existent_skill_returns_404(self, client: TestClient) -> None:
        _, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.patch(
            "/api/v1/profile/me/skills/999999",
            json={"proficiency_level": "advanced"},
            headers=headers,
        )
        assert resp.status_code == 404
