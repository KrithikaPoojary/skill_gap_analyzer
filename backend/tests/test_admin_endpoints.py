"""Integration tests for admin endpoints — verifies RBAC guards."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestAdminEndpoints:

    def _register(self, client: TestClient, superuser: bool = False) -> tuple[int, str]:
        email = f"adm{uuid.uuid4().hex[:6]}@test.com"
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Admin1234!"},
        )
        user_id = resp.json().get("data", {}).get("id") or resp.json().get("id")
        token_resp = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "Admin1234!"},
        )
        return user_id, token_resp.json()["access_token"]

    def test_list_users_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/api/v1/admin/users")
        assert resp.status_code == 401

    def test_list_users_requires_superuser(self, client: TestClient) -> None:
        _, token = self._register(client)
        resp = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_get_nonexistent_user_404(self, client: TestClient) -> None:
        from app.models.user import User
        from app.core.security import hash_password
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            su = User(
                email=f"su{uuid.uuid4().hex[:6]}@test.com",
                hashed_password=hash_password("Super1234!"),
                is_superuser=True,
                is_active=True,
            )
            db.add(su)
            db.commit()

        token_resp = client.post(
            "/api/v1/auth/login",
            data={"username": su.email, "password": "Super1234!"},
        )
        token = token_resp.json()["access_token"]

        resp = client.get(
            "/api/v1/admin/users/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_broadcast_requires_superuser(self, client: TestClient) -> None:
        _, token = self._register(client)
        resp = client.post(
            "/api/v1/admin/notifications/broadcast",
            params={"title": "Hello", "message": "World"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_search_users_requires_superuser(self, client: TestClient) -> None:
        _, token = self._register(client)
        resp = client.get(
            "/api/v1/admin/users/search",
            params={"email": "test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

