"""Tests for admin delete and promote user endpoints."""
from __future__ import annotations

import uuid
import pytest
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password


class TestAdminDeletePromote:

    def _create_superuser_token(self, client: TestClient) -> str:
        with SessionLocal() as db:
            su = User(
                email=f"su_{uuid.uuid4().hex[:6]}@test.com",
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

    def _create_plain_user_id(self, client: TestClient) -> int:
        email = f"plain_{uuid.uuid4().hex[:6]}@test.com"
        r = client.post("/api/v1/auth/register", json={"email": email, "password": "PlainPass1!"})
        return r.json()["id"]

    def test_delete_user_requires_superuser(self, client: TestClient) -> None:
        _, token = (lambda e: (e, client.post("/api/v1/auth/login",
            data={"username": e, "password": "PlainPass1!"}).json()["access_token"]))(
            client.post("/api/v1/auth/register",
                json={"email": f"del_{uuid.uuid4().hex[:6]}@t.com", "password": "PlainPass1!"}).json()["email"]
        )
        resp = client.delete(f"/api/v1/admin/users/999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_delete_nonexistent_user_returns_404(self, client: TestClient) -> None:
        token = self._create_superuser_token(client)
        resp = client.delete("/api/v1/admin/users/9999999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_delete_user_success(self, client: TestClient) -> None:
        token = self._create_superuser_token(client)
        user_id = self._create_plain_user_id(client)
        resp = client.delete(f"/api/v1/admin/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_promote_user_success(self, client: TestClient) -> None:
        token = self._create_superuser_token(client)
        user_id = self._create_plain_user_id(client)
        resp = client.patch(f"/api/v1/admin/users/{user_id}/promote", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["is_superuser"] is True
