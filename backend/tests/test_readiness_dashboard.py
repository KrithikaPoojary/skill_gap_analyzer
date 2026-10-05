"""Tests for the gap analysis readiness dashboard endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import RoleSkillWeighting, TargetRole
from app.models.skill import Skill


class TestReadinessDashboardEndpoint:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        email = f"readiness_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_readiness_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/gap-analysis/me/readiness")
        assert resp.status_code == 401

    def test_readiness_returns_dashboard(self, client: TestClient) -> None:
        user_id, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        suffix = uuid.uuid4().hex[:6]

        with SessionLocal() as db:
            s1 = Skill(name=f"TypeScript_{suffix}", normalized_name=f"typescript_{suffix}", category="frontend")
            s2 = Skill(name=f"React_{suffix}", normalized_name=f"react_{suffix}", category="frontend")
            role = TargetRole(
                title=f"Frontend Dev {suffix}",
                slug=f"frontend-dev-{suffix}",
                category="Frontend",
                is_active=True,
            )
            db.add_all([s1, s2, role])
            db.commit()
            db.refresh(s1); db.refresh(s2); db.refresh(role)

            db.add_all([
                RoleSkillWeighting(role_id=role.id, skill_id=s1.id, weight=0.6, is_core=True),
                RoleSkillWeighting(role_id=role.id, skill_id=s2.id, weight=0.4, is_core=True),
            ])
            db.commit()

        client.post(
            "/api/v1/profile/me/skills",
            json={"skill_name": f"TypeScript_{suffix}", "proficiency_level": "expert"},
            headers=headers,
        )

        resp = client.get("/api/v1/gap-analysis/me/readiness", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "user_id" in data
        assert "total_roles_evaluated" in data
        assert "roles" in data
        assert data["total_roles_evaluated"] >= 1

        role_entry = next((r for r in data["roles"] if r["role_id"] == role.id), None)
        assert role_entry is not None
        assert role_entry["readiness_score"] > 0
        assert "missing_count" in role_entry
