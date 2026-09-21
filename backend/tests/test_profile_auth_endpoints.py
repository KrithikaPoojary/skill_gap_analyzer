"""Integration tests for authenticated profile endpoints (/api/v1/profile/me)."""

from __future__ import annotations

import uuid
import pytest
from starlette.testclient import TestClient


class TestProfileAuthEndpoints:
    """Test suite for /api/v1/profile/me authenticated endpoints."""

    def _register_and_get_token(self, client: TestClient) -> tuple[str, str]:
        email = f"profile_user_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword123!"
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Profile Tester"},
        )
        assert reg_resp.status_code == 201

        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        return email, token

    def test_get_profile_me_unauthenticated_returns_401(self, client: TestClient):
        resp = client.get("/api/v1/profile/me")
        assert resp.status_code == 401

    def test_get_profile_me_authenticated(self, client: TestClient):
        email, token = self._register_and_get_token(client)
        resp = client.get(
            "/api/v1/profile/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        data = body["data"]
        assert data["email"] == email
        assert data["full_name"] == "Profile Tester"
        assert "profile" in data
        assert "skills" in data

    def test_update_profile_me_authenticated(self, client: TestClient):
        email, token = self._register_and_get_token(client)
        update_payload = {
            "headline": "Senior Cloud Engineer",
            "bio": "Passionate about distributed systems.",
            "years_of_experience": 5.5,
            "location": "San Francisco, CA",
            "github_url": "https://github.com/profiletester",
        }
        resp = client.put(
            "/api/v1/profile/me",
            json=update_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["headline"] == "Senior Cloud Engineer"
        assert data["years_of_experience"] == 5.5
        assert data["location"] == "San Francisco, CA"

        # Verify via GET /profile/me
        get_resp = client.get(
            "/api/v1/profile/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 200
        get_data = get_resp.json()["data"]
        assert get_data["profile"]["headline"] == "Senior Cloud Engineer"

    def test_add_and_remove_my_skill(self, client: TestClient):
        email, token = self._register_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Add Python skill
        add_resp = client.post(
            "/api/v1/profile/me/skills",
            json={
                "skill_name": "Python",
                "proficiency_level": "advanced",
                "years_of_experience": 4.0,
            },
            headers=headers,
        )
        assert add_resp.status_code == 201
        added_skill = add_resp.json()["data"]
        assert added_skill["name"] == "Python"
        skill_id = added_skill["skill_id"]

        # Verify skill appears in profile
        prof_resp = client.get("/api/v1/profile/me", headers=headers)
        assert prof_resp.status_code == 200
        profile_skills = prof_resp.json()["data"]["skills"]
        assert any(s["skill_id"] == skill_id for s in profile_skills)

        # Remove skill
        del_resp = client.delete(f"/api/v1/profile/me/skills/{skill_id}", headers=headers)
        assert del_resp.status_code == 200

        # Verify skill removed
        prof_resp2 = client.get("/api/v1/profile/me", headers=headers)
        profile_skills2 = prof_resp2.json()["data"]["skills"]
        assert not any(s["skill_id"] == skill_id for s in profile_skills2)

    def test_bulk_add_my_skills(self, client: TestClient):
        email, token = self._register_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        bulk_resp = client.post(
            "/api/v1/profile/me/skills/bulk",
            json={"skills": ["FastAPI", "Docker", "PostgreSQL"], "proficiency_level": "intermediate"},
            headers=headers,
        )
        assert bulk_resp.status_code == 201
        data = bulk_resp.json()["data"]
        assert data["added_count"] >= 1

    def test_get_profile_stats(self, client: TestClient):
        email, token = self._register_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/profile/me/stats", headers=headers)
        assert resp.status_code == 200
        stats = resp.json()["data"]
        assert "total_skills" in stats
        assert "avg_proficiency_score" in stats
        assert "profile_complete" in stats

