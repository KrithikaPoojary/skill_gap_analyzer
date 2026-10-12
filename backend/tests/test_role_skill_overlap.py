"""Tests for role skill overlap comparison endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient
from app.db.session import SessionLocal
from app.models.role import RoleSkillWeighting, TargetRole
from app.models.skill import Skill



class TestRoleSkillOverlap:
    """Tests for GET /api/v1/roles/{role_id}/overlap/{target_role_id}."""

    def test_overlap_role1_not_found(self, client: TestClient) -> None:
        res = client.get("/api/v1/roles/999999/overlap/1")
        assert res.status_code == 404

    def test_overlap_role2_not_found(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            r1 = TargetRole(
                title=f"DevOps Lead {suffix}",
                slug=f"devops-lead-{suffix}",
                description="DevOps role",
                category="engineering",
            )
            db.add(r1)
            db.commit()
            db.refresh(r1)
            r1_id = r1.id

        res = client.get(f"/api/v1/roles/{r1_id}/overlap/999999")
        assert res.status_code == 404


    def test_overlap_success_with_shared_and_unique(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            s_shared = Skill(name=f"Git VCS {suffix}", normalized_name=f"git_vcs_{suffix}", category="tools")
            s_r1 = Skill(name=f"Kubernetes {suffix}", normalized_name=f"k8s_{suffix}", category="devops")
            s_r2 = Skill(name=f"React JS {suffix}", normalized_name=f"react_js_{suffix}", category="frontend")
            db.add_all([s_shared, s_r1, s_r2])
            db.commit()

            role1 = TargetRole(
                title=f"SRE Role {suffix}",
                slug=f"sre-role-{suffix}",
                description="Site Reliability",
                category="infrastructure",
            )
            role2 = TargetRole(
                title=f"Fullstack Role {suffix}",
                slug=f"fullstack-role-{suffix}",
                description="Fullstack Dev",
                category="web",
            )
            db.add_all([role1, role2])
            db.commit()

            rs1 = RoleSkillWeighting(role_id=role1.id, skill_id=s_shared.id, is_core=True, weight=1.0)
            rs2 = RoleSkillWeighting(role_id=role1.id, skill_id=s_r1.id, is_core=True, weight=1.0)
            rs3 = RoleSkillWeighting(role_id=role2.id, skill_id=s_shared.id, is_core=False, weight=0.8)
            rs4 = RoleSkillWeighting(role_id=role2.id, skill_id=s_r2.id, is_core=True, weight=1.0)
            db.add_all([rs1, rs2, rs3, rs4])

            db.commit()

            r1_id = role1.id
            r2_id = role2.id

        res = client.get(f"/api/v1/roles/{r1_id}/overlap/{r2_id}")
        assert res.status_code == 200
        payload = res.json()
        assert payload["success"] is True
        data = payload["data"]

        assert data["shared_count"] == 1
        assert data["role1_unique_count"] == 1
        assert data["role2_unique_count"] == 1
        assert data["overlap_percentage"] > 0
        assert len(data["shared_skills"]) == 1
        assert data["shared_skills"][0]["skill_name"] == f"Git VCS {suffix}"
