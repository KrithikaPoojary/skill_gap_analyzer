"""Integration tests for target roles REST API (/api/v1/roles)."""

from __future__ import annotations

import uuid
import pytest
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import TargetRole


class TestRoleEndpoints:
    """Test suite for target roles endpoints."""

    def _register(self, client: TestClient) -> tuple[int, str]:
        email = f"roletester_{uuid.uuid4().hex[:6]}@example.com"
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "RolePassword123!"},
        )
        login = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "RolePassword123!"},
        )
        return login.json().get("user_id", 1), login.json()["access_token"]

    def test_list_target_roles_public(self, client: TestClient) -> None:
        resp = client.get("/api/v1/roles")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)

    def test_get_target_role_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/v1/roles/999999")
        assert resp.status_code == 404

    def test_get_target_role_by_slug_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/v1/roles/by-slug/nonexistent-role-slug-xyz")
        assert resp.status_code == 404

    def test_get_my_targets_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/roles/me/targets")
        assert resp.status_code == 401

    def test_track_and_untrack_target_role(self, client: TestClient) -> None:
        _, token = self._register(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create a test target role in db
        slug = f"test-role-{uuid.uuid4().hex[:6]}"
        with SessionLocal() as db:
            role = TargetRole(
                title=f"Test Role {slug}",
                slug=slug,
                description="A test engineering role.",
                category="Software Engineering",
                min_experience_years=2.0,
                is_active=True,
            )
            db.add(role)
            db.commit()
            db.refresh(role)
            role_id = role.id

        # Track target role
        track_resp = client.post(
            "/api/v1/roles/me/targets",
            json={"role_id": role_id},
            headers=headers,
        )
        assert track_resp.status_code == 201
        data = track_resp.json()["data"]
        assert data["role_id"] == role_id
        assert data["role_title"] == f"Test Role {slug}"

        # List my tracked roles
        list_resp = client.get("/api/v1/roles/me/targets", headers=headers)
        assert list_resp.status_code == 200
        my_roles = list_resp.json()["data"]
        assert any(r["role_id"] == role_id for r in my_roles)

        # Untrack target role
        del_resp = client.delete(f"/api/v1/roles/me/targets/{role_id}", headers=headers)
        assert del_resp.status_code == 200

        # Untrack again returns 404
        del_resp2 = client.delete(f"/api/v1/roles/me/targets/{role_id}", headers=headers)
        assert del_resp2.status_code == 404
