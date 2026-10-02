"""Tests for multi-role skill gap comparison endpoints."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestRoleComparison:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"cmp_{uuid.uuid4().hex[:6]}@test.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "PassWord123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "PassWord123!"}).json()["access_token"]
        return uid, tok

    def test_compare_roles_public(self, client: TestClient) -> None:
        payload = {
            "skills": ["Python", "FastAPI", "SQLAlchemy"],
            "roles": ["Backend Engineer", "Data Scientist"],
        }
        res = client.post("/api/v1/gap-analysis/compare", json=payload)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["skills_count"] == 3
        assert data["roles_evaluated"] == 2
        assert len(data["comparisons"]) == 2
        assert data["best_fit_role"] is not None

    def test_compare_roles_validation(self, client: TestClient) -> None:
        # Less than 2 roles should fail validation
        res = client.post("/api/v1/gap-analysis/compare", json={"roles": ["Backend Engineer"]})
        assert res.status_code == 422

    def test_compare_my_roles_unauthorized(self, client: TestClient) -> None:
        res = client.post("/api/v1/gap-analysis/me/compare", json={"roles": ["Backend Engineer", "DevOps Engineer"]})
        assert res.status_code == 401

    def test_compare_my_roles_success(self, client: TestClient) -> None:
        uid, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        res = client.post(
            "/api/v1/gap-analysis/me/compare",
            json={"roles": ["Backend Engineer", "Frontend Engineer"]},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["user_id"] == uid
        assert data["roles_evaluated"] == 2
        assert len(data["comparisons"]) == 2
