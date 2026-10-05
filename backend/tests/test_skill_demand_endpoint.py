"""Tests for GET /skills/{skill_id}/demand endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.models.associations import JobSkill, UserSkill
from app.models.job import JobPosting
from app.models.role import RoleSkillWeighting, TargetRole
from app.models.skill import Skill
from app.models.user import User
from sqlalchemy.orm import Session


class TestSkillDemandEndpoint:

    def test_skill_demand_not_found(self, client: TestClient) -> None:
        res = client.get("/api/v1/skills/999999/demand")
        assert res.status_code == 404

    def test_skill_demand_success(self, client: TestClient) -> None:
        with Session(engine) as db:
            uid = uuid.uuid4().hex[:6]
            # Create Skill
            skill = Skill(
                name=f"Kubernetes_{uid}",
                normalized_name=f"kubernetes_{uid}",
                category="cloud_devops",
                is_verified=True,
            )
            db.add(skill)
            db.flush()

            # Create Job requiring Skill
            job = JobPosting(
                title=f"Cloud Architect {uid}",
                company_name=f"CloudCorp {uid}",
                description="desc",
                is_active=True,
            )
            db.add(job)
            db.flush()

            js = JobSkill(job_id=job.id, skill_id=skill.id, is_required=True, importance_weight=4.5)
            db.add(js)

            # Create TargetRole requiring Skill
            role = TargetRole(
                title=f"DevOps Lead {uid}",
                slug=f"devops-lead-{uid}",
                category="Cloud",
                is_active=True,
            )
            db.add(role)
            db.flush()

            rsw = RoleSkillWeighting(role_id=role.id, skill_id=skill.id, weight=4.0, is_core=True)
            db.add(rsw)

            # Create User having Skill
            user = User(
                email=f"candidate_{uid}@example.com",
                hashed_password="pw",
                is_active=True,
            )
            db.add(user)
            db.flush()

            us = UserSkill(user_id=user.id, skill_id=skill.id, proficiency_level="advanced", years_of_experience=3.0)
            db.add(us)

            db.commit()
            skill_id = skill.id

        res = client.get(f"/api/v1/skills/{skill_id}/demand")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["skill_id"] == skill_id
        assert data["active_job_count"] >= 1
        assert data["avg_importance_weight"] >= 4.0
        assert data["target_roles_count"] >= 1
        assert data["candidates_count"] >= 1
        assert len(data["target_roles"]) >= 1
