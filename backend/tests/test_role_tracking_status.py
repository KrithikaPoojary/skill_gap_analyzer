"""Tests for GET /roles/me/targets/{role_id} endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.models.role import TargetRole
from sqlalchemy.orm import Session


class TestRoleTrackingStatus:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"track_status_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def _create_role(self) -> int:
        with Session(engine) as db:
            uid = uuid.uuid4().hex[:6]
            role = TargetRole(
                title=f"DevOps Architect {uid}",
                slug=f"devops-architect-{uid}",
                category="Cloud",
                min_experience_years=3.0,
                is_active=True,
            )
            db.add(role)
            db.commit()
            return role.id

    def test_role_not_tracked_returns_false(self, client: TestClient) -> None:
        _, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        role_id = self._create_role()

        res = client.get(f"/api/v1/roles/me/targets/{role_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_tracked"] is False
        assert data["role_id"] == role_id
        assert data["tracking"] is None

    def test_role_tracked_returns_details(self, client: TestClient) -> None:
        _, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        role_id = self._create_role()

        # Track the role
        track_res = client.post("/api/v1/roles/me/targets", json={"role_id": role_id}, headers=headers)
        assert track_res.status_code == 201

        res = client.get(f"/api/v1/roles/me/targets/{role_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_tracked"] is True
        assert data["role_id"] == role_id
        assert data["tracking"] is not None
        assert data["tracking"]["role_id"] == role_id
        assert "readiness_score" in data["tracking"]
