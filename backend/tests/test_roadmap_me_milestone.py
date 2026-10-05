"""Tests for PATCH /roadmaps/me/{roadmap_id}/milestones/{milestone_id} endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestRoadmapMeMilestone:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"rm_milestone_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_milestone_update_ownership_and_progress(self, client: TestClient) -> None:
        from sqlalchemy.orm import Session
        from app.db.session import engine
        from app.models.role import TargetRole, RoleSkillWeighting
        from app.models.skill import Skill

        with Session(engine) as db:
            uid = uuid.uuid4().hex[:6]
            s = Skill(name=f"Golang_{uid}", normalized_name=f"golang_{uid}", category="language")
            db.add(s)
            db.flush()
            role = TargetRole(
                title=f"Backend Specialist {uid}",
                slug=f"backend-specialist-{uid}",
                category="Engineering",
                is_active=True,
            )
            db.add(role)
            db.flush()
            rsw = RoleSkillWeighting(role_id=role.id, skill_id=s.id, weight=5.0, is_core=True)
            db.add(rsw)
            db.commit()
            role_id = role.id

        user_id_1, token_1 = self._login_user(client)
        user_id_2, token_2 = self._login_user(client)

        headers_1 = {"Authorization": f"Bearer {token_1}"}
        headers_2 = {"Authorization": f"Bearer {token_2}"}

        # User 1 creates roadmap
        res = client.post(
            "/api/v1/roadmaps/me",
            params={"role_id": role_id, "weekly_commitment_hours": 10},
            headers=headers_1,
        )
        assert res.status_code == 201
        roadmap = res.json()["data"]
        roadmap_id = roadmap["id"]
        assert len(roadmap["milestones"]) > 0
        milestone_id = roadmap["milestones"][0]["id"]

        # User 2 tries to update User 1's milestone -> 404 forbidden/not found
        res_fail = client.patch(
            f"/api/v1/roadmaps/me/{roadmap_id}/milestones/{milestone_id}",
            json={"is_completed": True},
            headers=headers_2,
        )
        assert res_fail.status_code == 404

        # User 1 successfully marks milestone completed
        res_ok = client.patch(
            f"/api/v1/roadmaps/me/{roadmap_id}/milestones/{milestone_id}",
            json={"is_completed": True},
            headers=headers_1,
        )
        assert res_ok.status_code == 200
        data = res_ok.json()["data"]
        assert data["milestone_id"] == milestone_id
        assert data["is_completed"] is True
        assert data["roadmap_milestones_completed"] >= 1
        assert data["roadmap_progress_percentage"] > 0
