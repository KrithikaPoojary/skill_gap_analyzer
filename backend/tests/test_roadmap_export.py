"""Tests for candidate learning roadmap export endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestRoadmapExport:
    """Tests for GET /api/v1/roadmaps/me/{roadmap_id}/export."""

    def _login_user(self, client: TestClient) -> str:
        email = f"rm_exp_{uuid.uuid4().hex[:6]}@example.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!", "full_name": "Roadmap User"})
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return tok

    def test_export_unauthenticated(self, client: TestClient) -> None:
        res = client.get("/api/v1/roadmaps/me/1/export")
        assert res.status_code == 401

    def test_export_not_found(self, client: TestClient) -> None:
        token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/v1/roadmaps/me/999999/export", headers=headers)
        assert res.status_code == 404

    def test_export_success(self, client: TestClient) -> None:
        token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create roadmap
        res_create = client.post(
            "/api/v1/roadmaps/me",
            params={"role_name": "DevOps Engineer", "weekly_commitment_hours": 12},
            headers=headers,
        )
        assert res_create.status_code == 201
        roadmap_id = res_create.json()["data"]["id"]

        # Export roadmap
        res = client.get(f"/api/v1/roadmaps/me/{roadmap_id}/export", headers=headers)
        assert res.status_code == 200
        payload = res.json()
        assert payload["success"] is True
        data = payload["data"]

        assert data["roadmap_id"] == roadmap_id
        assert "exported_at" in data
        assert "candidate" in data
        assert data["candidate"]["full_name"] == "Roadmap User"
        assert "weekly_commitment_hours" in data
        assert "total_milestones" in data
        assert "curriculum" in data
        assert isinstance(data["curriculum"], list)
