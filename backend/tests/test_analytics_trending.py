"""Tests for analytics trending skills endpoint."""

from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill, SkillCategory


def test_get_trending_skills(client: TestClient) -> None:
    with SessionLocal() as db:
        # Create a skill and job posting
        s = Skill(
            name="Rust_Trend_Test",
            normalized_name="rust_trend_test",
            category=SkillCategory.LANGUAGE.value,
        )
        job = JobPosting(
            title="Rust Systems Engineer",
            company_name="RustCorp",
            description="High performance systems",
            is_active=True,
        )
        db.add_all([s, job])
        db.commit()
        db.refresh(s)
        db.refresh(job)

        js = JobSkill(
            job_id=job.id,
            skill_id=s.id,
            importance_weight=4.5,
            is_required=True,
        )
        db.add(js)
        db.commit()

    resp = client.get("/api/v1/analytics/skills/trending?limit=10&min_importance=4.0")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["success"] is True
    data = payload["data"]
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "skill_name" in first
        assert "rank" in first
        assert "avg_importance" in first
        assert first["avg_importance"] >= 4.0
