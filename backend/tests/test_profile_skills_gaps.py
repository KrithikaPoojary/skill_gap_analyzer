"""Tests for GET /profile/me/skills/gaps endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import TargetRole, RoleSkillWeighting, UserTargetRole
from app.models.skill import Skill, SkillCategory


class TestProfileSkillGaps:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"gaps_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_get_my_skill_gaps(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        tag = uuid.uuid4().hex[:6]

        with SessionLocal() as db:
            s_possessed = Skill(name=f"Python {tag}", normalized_name=f"python-{tag}", category=SkillCategory.LANGUAGE.value)
            s_missing1 = Skill(name=f"Rust {tag}", normalized_name=f"rust-{tag}", category=SkillCategory.LANGUAGE.value)
            s_missing2 = Skill(name=f"Kubernetes {tag}", normalized_name=f"k8s-{tag}", category=SkillCategory.CLOUD_DEVOPS.value)
            db.add_all([s_possessed, s_missing1, s_missing2])
            db.commit()
            db.refresh(s_possessed)
            db.refresh(s_missing1)
            db.refresh(s_missing2)

            role = TargetRole(title=f"Systems Engineer {tag}", slug=f"sys-eng-{tag}", description="Systems Role")
            db.add(role)
            db.commit()
            db.refresh(role)

            w1 = RoleSkillWeighting(role_id=role.id, skill_id=s_possessed.id, weight=3.0, is_core=True)
            w2 = RoleSkillWeighting(role_id=role.id, skill_id=s_missing1.id, weight=4.0, is_core=True)
            w3 = RoleSkillWeighting(role_id=role.id, skill_id=s_missing2.id, weight=2.0, is_core=False)
            db.add_all([w1, w2, w3])

            utr = UserTargetRole(user_id=user_id, role_id=role.id, readiness_score=33.3)
            db.add(utr)
            db.commit()

            s_poss_id = s_possessed.id

        # User adds s_possessed
        client.post(
            "/api/v1/profile/me/skills",
            json={"skill_id": s_poss_id, "proficiency_level": "advanced", "years_of_experience": 3.0},
            headers=headers,
        )

        # Call /profile/me/skills/gaps
        res = client.get("/api/v1/profile/me/skills/gaps", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_tracked_roles"] == 1
        assert data["total_missing_unique_skills"] == 2
        missing_names = [m["name"] for m in data["missing_skills"]]
        assert f"Rust {tag}" in missing_names
        assert f"Kubernetes {tag}" in missing_names
        assert f"Python {tag}" not in missing_names
