"""Tests for remote job breakdown analytics endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient
from app.db.session import SessionLocal
from app.models.job import JobPosting


class TestAnalyticsRemoteBreakdown:
    """Tests for GET /api/v1/analytics/jobs/remote-breakdown."""

    def test_remote_breakdown_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analytics/jobs/remote-breakdown")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["success"] is True
        data = payload["data"]

        assert "total_active_jobs" in data
        assert "total_remote" in data
        assert "total_onsite" in data
        assert "overall_remote_percentage" in data
        assert "by_experience_level" in data
        assert "by_employment_type" in data
        assert isinstance(data["by_experience_level"], list)
        assert isinstance(data["by_employment_type"], list)

    def test_remote_breakdown_with_new_jobs(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            j1 = JobPosting(
                title=f"Remote Engineer {suffix}",
                company_name=f"Remote Co {suffix}",
                description="desc",
                is_remote=True,
                experience_level="lead",
                employment_type="full_time",
            )
            j2 = JobPosting(
                title=f"Onsite Engineer {suffix}",
                company_name=f"Onsite Co {suffix}",
                description="desc",
                is_remote=False,
                experience_level="lead",
                employment_type="contract",
            )
            db.add_all([j1, j2])
            db.commit()

        resp = client.get("/api/v1/analytics/jobs/remote-breakdown")
        assert resp.status_code == 200
        data = resp.json()["data"]

        assert data["total_active_jobs"] >= 2
        assert data["total_remote"] >= 1
        assert data["total_onsite"] >= 1

        lead_stat = next((e for e in data["by_experience_level"] if e["experience_level"] == "lead"), None)
        assert lead_stat is not None
        assert lead_stat["total_jobs"] >= 2
        assert lead_stat["remote_jobs"] >= 1
