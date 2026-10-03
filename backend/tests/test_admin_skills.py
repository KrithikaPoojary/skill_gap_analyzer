"""Tests for admin skill management endpoints."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


class TestAdminSkills:

    def _create_superuser_token(self, client: TestClient) -> str:
        with SessionLocal() as db:
            su = User(
                email=f"su_skill_{uuid.uuid4().hex[:6]}@test.com",
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
        email = f"user_skill_{uuid.uuid4().hex[:6]}@test.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "UserPass1!"})
        resp = client.post("/api/v1/auth/login", data={"username": email, "password": "UserPass1!"})
        return resp.json()["access_token"]

    def test_create_skill_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.post("/api/v1/admin/skills", json={"name": "RustLang"})
        assert resp.status_code == 401

    def test_create_skill_regular_user_returns_403(self, client: TestClient) -> None:
        token = self._create_regular_user_token(client)
        resp = client.post(
            "/api/v1/admin/skills",
            json={"name": "RustLang"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_create_skill_lifecycle_success(self, client: TestClient) -> None:
        token = self._create_superuser_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        unique_name = f"GoFramework_{uuid.uuid4().hex[:6]}"

        # 1. Create skill
        resp = client.post(
            "/api/v1/admin/skills",
            json={
                "name": unique_name,
                "category": "framework",
                "description": "Golang web framework",
                "is_verified": True,
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        skill_id = data["id"]
        assert data["name"] == unique_name
        assert data["category"] == "framework"

        # 2. Duplicate create returns 409
        dup_resp = client.post(
            "/api/v1/admin/skills",
            json={"name": unique_name, "category": "framework"},
            headers=headers,
        )
        assert dup_resp.status_code == 409

        # 3. Update skill
        patch_resp = client.patch(
            f"/api/v1/admin/skills/{skill_id}",
            json={"description": "Updated description", "category": "language"},
            headers=headers,
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["category"] == "language"

        # 4. Delete skill
        del_resp = client.delete(f"/api/v1/admin/skills/{skill_id}", headers=headers)
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True
