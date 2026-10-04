"""Tests for GET /roles/{role_id}/skills endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import TargetRole, RoleSkillWeighting
from app.models.skill import Skill, SkillCategory


class TestRoleSkillsEndpoint:

    def test_get_role_skills_success(self, client: TestClient) -> None:
        tag = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            s1 = Skill(name=f"GraphQL {tag}", normalized_name=f"graphql-{tag}", category=SkillCategory.FRAMEWORK.value)
            s2 = Skill(name=f"TypeScript {tag}", normalized_name=f"typescript-{tag}", category=SkillCategory.LANGUAGE.value)
            db.add_all([s1, s2])
            db.commit()
            db.refresh(s1)
            db.refresh(s2)

            role = TargetRole(title=f"Fullstack Dev {tag}", slug=f"fullstack-dev-{tag}", description="Fullstack role")
            db.add(role)
            db.commit()
            db.refresh(role)

            w1 = RoleSkillWeighting(role_id=role.id, skill_id=s1.id, weight=3.5, is_core=False, benchmark_level="intermediate")
            w2 = RoleSkillWeighting(role_id=role.id, skill_id=s2.id, weight=5.0, is_core=True, benchmark_level="expert")
            db.add_all([w1, w2])
            db.commit()
            role_id = role.id

        res = client.get(f"/api/v1/roles/{role_id}/skills")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["role_id"] == role_id
        assert data["total_skills"] == 2
        skills = data["skills"]
        # Core skill should come first
        assert skills[0]["skill_name"] == f"TypeScript {tag}"
        assert skills[0]["is_core"] is True
        assert skills[1]["skill_name"] == f"GraphQL {tag}"

    def test_get_role_skills_not_found(self, client: TestClient) -> None:
        res = client.get("/api/v1/roles/999999/skills")
        assert res.status_code == 404
