"""Tests for roadmap progress summary endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient


class TestRoadmapProgress:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"progress_user_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_progress_empty_roadmaps(self, client: TestClient) -> None:
        _, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/v1/roadmaps/me/progress", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_roadmaps"] == 0
        assert data["overall_completion_percentage"] == 0.0

    def test_progress_with_created_roadmap(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create roadmap
        res = client.post(
            "/api/v1/roadmaps/me",
            params={"role_name": "DevOps Engineer", "weekly_commitment_hours": 12},
            headers=headers,
        )
        assert res.status_code == 201

        # Check progress
        res_prog = client.get("/api/v1/roadmaps/me/progress", headers=headers)
        assert res_prog.status_code == 200
        data = res_prog.json()["data"]
        assert data["total_roadmaps"] >= 1
        assert data["active_roadmaps"] >= 1
        assert data["total_milestones"] >= 0
        assert "overall_completion_percentage" in data
