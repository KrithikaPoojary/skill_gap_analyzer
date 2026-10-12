"""Tests for related skills co-occurrence endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient
from app.db.session import SessionLocal
from app.models.skill import Skill
from app.models.job import JobPosting
from app.models.associations import JobSkill


class TestSkillRelated:
    """Tests for GET /api/v1/skills/{skill_id}/related."""

    def test_related_skills_not_found(self, client: TestClient) -> None:
        res = client.get("/api/v1/skills/999999/related")
        assert res.status_code == 404

    def test_related_skills_empty(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            s = Skill(name=f"Solitary Skill {suffix}", normalized_name=f"solitary_skill_{suffix}", category="tools")
            db.add(s)
            db.commit()
            db.refresh(s)
            skill_id = s.id

        res = client.get(f"/api/v1/skills/{skill_id}/related")
        assert res.status_code == 200
        payload = res.json()
        assert payload["success"] is True
        data = payload["data"]
        assert data["skill_id"] == skill_id
        assert data["total_related"] == 0
        assert data["related_skills"] == []

    def test_related_skills_with_co_occurrence(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            s1 = Skill(name=f"PyLang {suffix}", normalized_name=f"pylang_{suffix}", category="languages")
            s2 = Skill(name=f"FastAPI FW {suffix}", normalized_name=f"fastapi_fw_{suffix}", category="frameworks")
            s3 = Skill(name=f"Docker Tool {suffix}", normalized_name=f"docker_tool_{suffix}", category="devops")
            db.add_all([s1, s2, s3])
            db.commit()
            db.refresh(s1)
            db.refresh(s2)
            db.refresh(s3)

            job = JobPosting(
                title=f"Backend Engineer {suffix}",
                company_name=f"TechCorp {suffix}",
                description="Python, FastAPI, and Docker required",
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            js1 = JobSkill(job_id=job.id, skill_id=s1.id, is_required=True, importance_weight=5.0)
            js2 = JobSkill(job_id=job.id, skill_id=s2.id, is_required=True, importance_weight=4.0)
            js3 = JobSkill(job_id=job.id, skill_id=s3.id, is_required=False, importance_weight=3.0)
            db.add_all([js1, js2, js3])
            db.commit()

            skill1_id = s1.id

        res = client.get(f"/api/v1/skills/{skill1_id}/related?limit=5")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_related"] >= 2
        rel_ids = [r["skill_id"] for r in data["related_skills"]]
        assert s2.id in rel_ids
        assert s3.id in rel_ids
        assert skill1_id not in rel_ids
