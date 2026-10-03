"""Tests for GET /roadmaps/me/{roadmap_id} endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestRoadmapMeGetDetails:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"rm_get_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_get_my_roadmap_details_success_and_isolation(self, client: TestClient) -> None:
        u1_id, u1_tok = self._login_user(client)
        h1 = {"Authorization": f"Bearer {u1_tok}"}

        # 1. Create a roadmap for user 1
        res = client.post(
            "/api/v1/roadmaps/me",
            params={"role_name": "Backend Engineer", "weekly_commitment_hours": 15},
            headers=h1,
        )
        assert res.status_code == 201
        roadmap_id = res.json()["data"]["id"]

        # 2. User 1 fetches roadmap details
        res_get = client.get(f"/api/v1/roadmaps/me/{roadmap_id}", headers=h1)
        assert res_get.status_code == 200
        data = res_get.json()["data"]
        assert data["id"] == roadmap_id
        assert data["user_id"] == u1_id
        assert "milestones" in data

        # 3. User 2 cannot access user 1's roadmap
        u2_id, u2_tok = self._login_user(client)
        h2 = {"Authorization": f"Bearer {u2_tok}"}
        res_other = client.get(f"/api/v1/roadmaps/me/{roadmap_id}", headers=h2)
        assert res_other.status_code == 404

        # 4. Non-existent roadmap returns 404
        res_none = client.get("/api/v1/roadmaps/me/999999", headers=h1)
        assert res_none.status_code == 404
