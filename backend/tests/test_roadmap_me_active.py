"""Tests for GET /roadmaps/me/active endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestRoadmapMeActive:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"active_rm_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_no_active_roadmap_returns_false(self, client: TestClient) -> None:
        _, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/roadmaps/me/active", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["has_active_roadmap"] is False
        assert data["roadmap"] is None

    def test_active_roadmap_returned(self, client: TestClient) -> None:
        _, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create roadmap (defaults to active)
        create_res = client.post(
            "/api/v1/roadmaps/me",
            params={"role_name": "Data Scientist", "weekly_commitment_hours": 10},
            headers=headers,
        )
        assert create_res.status_code == 201
        roadmap_id = create_res.json()["data"]["id"]

        res = client.get("/api/v1/roadmaps/me/active", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["has_active_roadmap"] is True
        assert data["roadmap"]["id"] == roadmap_id
        assert data["roadmap"]["status"] == "active"
