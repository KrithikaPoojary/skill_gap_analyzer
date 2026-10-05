"""Tests for quick-win career recommendations endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.associations import UserSkill
from app.models.role import RoleSkillWeighting, TargetRole
from app.models.skill import Skill


class TestRecommendationsQuickWins:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"quick_win_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_get_quick_wins_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/recommendations/me/quick-wins")
        assert resp.status_code == 401

    def test_get_quick_wins_authenticated(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            s1 = Skill(name=f"Python_{suffix}", normalized_name=f"python_{suffix}", category="backend")
            s2 = Skill(name=f"FastAPI_{suffix}", normalized_name=f"fastapi_{suffix}", category="backend")
            s3 = Skill(name=f"Kubernetes_{suffix}", normalized_name=f"kubernetes_{suffix}", category="devops")
            role = TargetRole(
                title=f"Python Developer {suffix}",
                slug=f"python-dev-{suffix}",
                category="Backend",
                is_active=True,
            )
            db.add_all([s1, s2, s3, role])
            db.commit()
            db.refresh(s1)
            db.refresh(s2)
            db.refresh(s3)
            db.refresh(role)

            rw1 = RoleSkillWeighting(role_id=role.id, skill_id=s1.id, weight=0.5, is_core=True)
            rw2 = RoleSkillWeighting(role_id=role.id, skill_id=s2.id, weight=0.5, is_core=True)
            db.add_all([rw1, rw2])
            db.commit()

        # Add skill to candidate profile via endpoint
        add_skill_res = client.post(
            "/api/v1/profile/me/skills",
            json={"skill_name": f"Python_{suffix}", "proficiency_level": "expert"},
            headers=headers,
        )
        assert add_skill_res.status_code in (200, 201)

        resp = client.get("/api/v1/recommendations/me/quick-wins", headers=headers)
        assert resp.status_code == 200
        payload = resp.json()["data"]
        assert payload["total"] >= 1
        qw = next(r for r in payload["quick_wins"] if r["role_id"] == role.id)
        assert len(qw["missing_skills"]) <= 2
        assert len(qw["matched_skills"]) > 0
