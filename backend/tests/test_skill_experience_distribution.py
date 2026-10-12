"""Tests for skill experience distribution endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient
from app.db.session import SessionLocal
from app.models.skill import Skill
from app.models.job import JobPosting
from app.models.associations import JobSkill


class TestSkillExperienceDistribution:
    """Tests for GET /api/v1/skills/{skill_id}/experience-distribution."""

    def test_experience_distribution_not_found(self, client: TestClient) -> None:
        res = client.get("/api/v1/skills/999999/experience-distribution")
        assert res.status_code == 404

    def test_experience_distribution_empty(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            s = Skill(name=f"Isolated Skill {suffix}", normalized_name=f"isolated_skill_{suffix}", category="tools")
            db.add(s)
            db.commit()
            db.refresh(s)
            skill_id = s.id

        res = client.get(f"/api/v1/skills/{skill_id}/experience-distribution")
        assert res.status_code == 200
        payload = res.json()
        assert payload["success"] is True
        data = payload["data"]
        assert data["skill_id"] == skill_id
        assert data["total_postings"] == 0
        assert data["distribution"] == []

    def test_experience_distribution_with_jobs(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            s = Skill(name=f"GoLang {suffix}", normalized_name=f"golang_{suffix}", category="languages")
            db.add(s)
            db.commit()
            db.refresh(s)

            j1 = JobPosting(
                title=f"Senior Go Dev {suffix}",
                company_name=f"CloudCorp {suffix}",
                description="desc",
                experience_level="senior",
            )
            j2 = JobPosting(
                title=f"Mid Go Dev {suffix}",
                company_name=f"CloudCorp {suffix}",
                description="desc",
                experience_level="mid",
            )
            db.add_all([j1, j2])
            db.commit()

            js1 = JobSkill(job_id=j1.id, skill_id=s.id)
            js2 = JobSkill(job_id=j2.id, skill_id=s.id)
            db.add_all([js1, js2])
            db.commit()

            skill_id = s.id

        res = client.get(f"/api/v1/skills/{skill_id}/experience-distribution")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_postings"] == 2
        levels = {d["experience_level"]: d for d in data["distribution"]}
        assert "senior" in levels
        assert "mid" in levels
        assert levels["senior"]["count"] == 1
        assert levels["mid"]["count"] == 1
