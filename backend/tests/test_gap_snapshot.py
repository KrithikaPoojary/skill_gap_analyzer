"""Integration tests for skill gap historical snapshots (/api/v1/gap-analysis/me/history)."""

from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import TargetRole


class TestGapSnapshotEndpoints:
    """Test suite for skill gap snapshot history endpoints."""

    def _register_and_get_token(self, client: TestClient) -> tuple[int, str]:
        email = f"snapshot_user_{uuid.uuid4().hex[:6]}@example.com"
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "SnapshotPass123!"},
        )
        login = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "SnapshotPass123!"},
        )
        return login.json().get("user_id", 1), login.json()["access_token"]

    def test_get_history_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/gap-analysis/me/history")
        assert resp.status_code == 401

    def test_save_snapshot_and_list_history(self, client: TestClient) -> None:
        _, token = self._register_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create target role in DB
        slug = f"hist-role-{uuid.uuid4().hex[:6]}"
        with SessionLocal() as db:
            role = TargetRole(
                title=f"History Role {slug}",
                slug=slug,
                description="A test role for history snapshot.",
                category="Software Engineering",
                min_experience_years=2.0,
                is_active=True,
            )
            db.add(role)
            db.commit()
            db.refresh(role)
            role_id = role.id

        # Save snapshot
        snap_resp = client.post(
            "/api/v1/gap-analysis/me/snapshot",
            params={"role_id": role_id},
            headers=headers,
        )
        assert snap_resp.status_code == 201
        snap_data = snap_resp.json()["data"]
        snapshot_id = snap_data["id"]
        assert snap_data["role_id"] == role_id
        assert "readiness_score" in snap_data

        # List history
        hist_resp = client.get("/api/v1/gap-analysis/me/history", headers=headers)
        assert hist_resp.status_code == 200
        history_items = hist_resp.json()["data"]
        assert any(h["id"] == snapshot_id for h in history_items)

        # Delete snapshot
        del_resp = client.delete(
            f"/api/v1/gap-analysis/me/history/{snapshot_id}", headers=headers
        )
        assert del_resp.status_code == 200

        # Delete again returns 404
        del_resp2 = client.delete(
            f"/api/v1/gap-analysis/me/history/{snapshot_id}", headers=headers
        )
        assert del_resp2.status_code == 404
