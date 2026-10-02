"""Tests for admin platform-wide stats overview endpoint."""
from __future__ import annotations

import uuid
import pytest
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password


class TestAdminStats:

    def _create_superuser_token(self, client: TestClient) -> str:
        with SessionLocal() as db:
            su = User(
                email=f"su_stats_{uuid.uuid4().hex[:6]}@test.com",
                hashed_password=hash_password("SuperPass1!"),
                is_superuser=True,
                is_active=True,
            )
            db.add(su)
            db.commit()
            db.refresh(su)
            email = su.email
        resp = client.post("/api/v1/auth/login", data={"username": email, "password": "SuperPass1!"})
        return resp.json()["access_token"]

    def test_stats_overview_requires_superuser(self, client: TestClient) -> None:
        email = f"plain_stats_{uuid.uuid4().hex[:6]}@t.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "PlainPass1!"})
        login_res = client.post("/api/v1/auth/login", data={"username": email, "password": "PlainPass1!"})
        token = login_res.json()["access_token"]

        resp = client.get("/api/v1/admin/stats/overview", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_stats_overview_success(self, client: TestClient) -> None:
        token = self._create_superuser_token(client)
        resp = client.get("/api/v1/admin/stats/overview", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "jobs" in data
        assert "skills" in data
        assert "roles" in data
        assert "gap_analysis" in data
        assert "notifications" in data

        assert "total_users" in data["users"]
        assert "active_users" in data["users"]
        assert data["users"]["superuser_count"] >= 1
