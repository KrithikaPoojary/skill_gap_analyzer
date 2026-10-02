"""Tests for authenticated user roadmap lifecycle (status update and deletion)."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestRoadmapMeLifecycle:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"user_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_update_status_and_delete_roadmap(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create a roadmap
        res = client.post(
            "/api/v1/roadmaps/me",
            params={"role_name": "Backend Engineer", "weekly_commitment_hours": 15},
            headers=headers,
        )
        assert res.status_code == 201
        roadmap_id = res.json()["data"]["id"]

        # 2. Update status to paused
        res_patch = client.patch(
            f"/api/v1/roadmaps/me/{roadmap_id}/status",
            params={"status": "paused"},
            headers=headers,
        )
        assert res_patch.status_code == 200
        assert res_patch.json()["data"]["status"] == "paused"

        # 3. Another user cannot update or delete it
        _, token2 = self._login_user(client)
        headers2 = {"Authorization": f"Bearer {token2}"}
        res_other = client.patch(
            f"/api/v1/roadmaps/me/{roadmap_id}/status",
            params={"status": "archived"},
            headers=headers2,
        )
        assert res_other.status_code == 404

        res_del_other = client.delete(
            f"/api/v1/roadmaps/me/{roadmap_id}",
            headers=headers2,
        )
        assert res_del_other.status_code == 404

        # 4. Owner deletes it
        res_del = client.delete(
            f"/api/v1/roadmaps/me/{roadmap_id}",
            headers=headers,
        )
        assert res_del.status_code == 200
        assert res_del.json()["data"]["deleted"] is True

        # 5. Subsequent delete returns 404
        res_del_again = client.delete(
            f"/api/v1/roadmaps/me/{roadmap_id}",
            headers=headers,
        )
        assert res_del_again.status_code == 404
