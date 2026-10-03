"""Tests for admin user export endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password


class TestAdminUserExport:

    def _create_superuser_token(self, client: TestClient) -> str:
        with SessionLocal() as db:
            su = User(
                email=f"su_exp_{uuid.uuid4().hex[:6]}@test.com",
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

    def _create_regular_user_token(self, client: TestClient) -> str:
        email = f"user_exp_{uuid.uuid4().hex[:6]}@test.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "UserPass1!"})
        resp = client.post("/api/v1/auth/login", data={"username": email, "password": "UserPass1!"})
        return resp.json()["access_token"]

    def test_export_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/admin/users/export")
        assert resp.status_code == 401

    def test_export_non_superuser_returns_403(self, client: TestClient) -> None:
        token = self._create_regular_user_token(client)
        resp = client.get("/api/v1/admin/users/export", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_export_json_success(self, client: TestClient) -> None:
        token = self._create_superuser_token(client)
        resp = client.get("/api/v1/admin/users/export?format=json", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "users" in data
        assert isinstance(data["users"], list)
        if data["users"]:
            user_entry = data["users"][0]
            assert "email" in user_entry
            assert "login_count" in user_entry

    def test_export_csv_success(self, client: TestClient) -> None:
        token = self._create_superuser_token(client)
        resp = client.get("/api/v1/admin/users/export?format=csv", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        assert "attachment" in resp.headers.get("content-disposition", "")
        content = resp.text
        assert "id,email,full_name,is_active,is_superuser,login_count,last_login_at,created_at" in content
