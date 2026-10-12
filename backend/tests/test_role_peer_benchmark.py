"""Tests for role peer benchmark gap analysis endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import TargetRole, UserTargetRole
from app.models.user import User


class TestRolePeerBenchmarkEndpoint:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        email = f"benchmark_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/gap-analysis/benchmark/1")
        assert resp.status_code == 401

    def test_role_not_found_returns_404(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        resp = client.get(
            "/api/v1/gap-analysis/benchmark/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_role_benchmark_with_cohort(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        suffix = uuid.uuid4().hex[:6]

        with SessionLocal() as db:
            role = TargetRole(
                title=f"Benchmark Engineer {suffix}",
                slug=f"benchmark-eng-{suffix}",
                category="Engineering",
                is_active=True,
            )
            u1 = User(email=f"peer1_{suffix}@test.com", hashed_password="pw")
            u2 = User(email=f"peer2_{suffix}@test.com", hashed_password="pw")
            db.add_all([role, u1, u2])
            db.commit()
            db.refresh(role)
            db.refresh(u1)
            db.refresh(u2)

            ut1 = UserTargetRole(user_id=u1.id, role_id=role.id, readiness_score=40.0)
            ut2 = UserTargetRole(user_id=u2.id, role_id=role.id, readiness_score=80.0)
            db.add_all([ut1, ut2])
            db.commit()
            role_id = role.id

        resp = client.get(
            f"/api/v1/gap-analysis/benchmark/{role_id}",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["role_id"] == role_id
        assert data["cohort_size"] == 3
        assert isinstance(data["average_readiness_score"], float)
        assert data["max_readiness_score"] == 80.0
        assert "percentile_rank" in data
        assert "is_above_average" in data
