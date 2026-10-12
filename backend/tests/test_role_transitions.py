"""Tests for role career transitions recommendation endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient
from app.db.session import SessionLocal
from app.models.role import RoleSkillWeighting, TargetRole
from app.models.skill import Skill


class TestRoleTransitions:
    """Tests for GET /api/v1/roles/{role_id}/transitions."""

    def test_transitions_not_found(self, client: TestClient) -> None:
        res = client.get("/api/v1/roles/999999/transitions")
        assert res.status_code == 404

    def test_transitions_empty(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            role = TargetRole(
                title=f"Isolated Role {suffix}",
                slug=f"isolated-role-{suffix}",
                description="desc",
                category="other",
            )
            db.add(role)
            db.commit()
            db.refresh(role)
            role_id = role.id

        res = client.get(f"/api/v1/roles/{role_id}/transitions")
        assert res.status_code == 200
        payload = res.json()
        assert payload["success"] is True
        data = payload["data"]
        assert data["source_role"]["id"] == role_id
        assert data["total_recommendations"] == 0
        assert data["transitions"] == []

    def test_transitions_recommendations_ranking(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            s1 = Skill(name=f"Python {suffix}", normalized_name=f"py_{suffix}", category="languages")
            s2 = Skill(name=f"SQL {suffix}", normalized_name=f"sql_{suffix}", category="databases")
            s3 = Skill(name=f"Spark {suffix}", normalized_name=f"spark_{suffix}", category="data")
            db.add_all([s1, s2, s3])
            db.commit()

            # Source role has Python and SQL
            source_role = TargetRole(
                title=f"Junior Backend {suffix}",
                slug=f"jr-backend-{suffix}",
                description="desc",
                category="engineering",
            )
            # Target role has Python, SQL, and Spark (2/3 match = 66.7%)
            target_role = TargetRole(
                title=f"Data Engineer {suffix}",
                slug=f"data-eng-{suffix}",
                description="desc",
                category="data",
            )
            db.add_all([source_role, target_role])
            db.commit()

            rw1 = RoleSkillWeighting(role_id=source_role.id, skill_id=s1.id, is_core=True)
            rw2 = RoleSkillWeighting(role_id=source_role.id, skill_id=s2.id, is_core=True)
            rw3 = RoleSkillWeighting(role_id=target_role.id, skill_id=s1.id, is_core=True)
            rw4 = RoleSkillWeighting(role_id=target_role.id, skill_id=s2.id, is_core=True)
            rw5 = RoleSkillWeighting(role_id=target_role.id, skill_id=s3.id, is_core=True)
            db.add_all([rw1, rw2, rw3, rw4, rw5])
            db.commit()

            source_id = source_role.id
            target_id = target_role.id

        res = client.get(f"/api/v1/roles/{source_id}/transitions?limit=5")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_recommendations"] >= 1
        rec = next((r for r in data["transitions"] if r["role_id"] == target_id), None)
        assert rec is not None
        assert rec["shared_skills_count"] == 2
        assert rec["total_target_skills"] == 3
        assert rec["transferability_pct"] == 66.7
