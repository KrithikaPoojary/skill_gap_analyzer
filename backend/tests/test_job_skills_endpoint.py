"""Tests for GET /jobs/{job_id}/skills endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill
from sqlalchemy.orm import Session


class TestJobSkillsEndpoint:

    def test_job_skills_not_found(self, client: TestClient) -> None:
        res = client.get("/api/v1/jobs/999999/skills")
        assert res.status_code == 404
        assert res.json()["success"] is False or "error" in res.json()

    def test_job_skills_success(self, client: TestClient) -> None:
        with Session(engine) as db:
            uid = uuid.uuid4().hex[:6]
            s1 = Skill(name=f"Python_{uid}", normalized_name=f"python_{uid}", category="language")
            s2 = Skill(name=f"Docker_{uid}", normalized_name=f"docker_{uid}", category="cloud_devops")
            db.add_all([s1, s2])
            db.flush()

            job = JobPosting(
                title=f"Backend Engineer {uid}",
                company_name=f"TechCorp {uid}",
                description="Python backend position",
                is_active=True,
            )
            db.add(job)
            db.flush()

            js1 = JobSkill(job_id=job.id, skill_id=s1.id, is_required=True, importance_weight=5.0)
            js2 = JobSkill(job_id=job.id, skill_id=s2.id, is_required=False, importance_weight=3.0)
            db.add_all([js1, js2])
            db.commit()
            job_id = job.id
            s1_id = s1.id
            s2_id = s2.id

        res = client.get(f"/api/v1/jobs/{job_id}/skills")
        assert res.status_code == 200
        payload = res.json()["data"]
        assert payload["job_id"] == job_id
        assert payload["total_skills"] == 2
        skills = payload["skills"]
        assert len(skills) == 2

        # Check required first due to ordering
        assert skills[0]["skill_id"] == s1_id
        assert skills[0]["is_required"] is True
        assert skills[0]["importance_weight"] == 5.0
        assert skills[1]["skill_id"] == s2_id
        assert skills[1]["is_required"] is False
