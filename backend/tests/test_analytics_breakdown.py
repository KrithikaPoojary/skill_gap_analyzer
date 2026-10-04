"""Tests for GET /analytics/breakdown endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.models.job import JobPosting
from sqlalchemy.orm import Session


class TestAnalyticsBreakdown:

    def test_analytics_breakdown_success(self, client: TestClient) -> None:
        with Session(engine) as db:
            uid = uuid.uuid4().hex[:6]
            j1 = JobPosting(
                title=f"Engineer 1 {uid}",
                company_name=f"Comp1 {uid}",
                description="desc",
                employment_type="full_time",
                experience_level="mid",
                is_active=True,
            )
            j2 = JobPosting(
                title=f"Engineer 2 {uid}",
                company_name=f"Comp2 {uid}",
                description="desc",
                employment_type="contract",
                experience_level="senior",
                is_active=True,
            )
            db.add_all([j1, j2])
            db.commit()

        res = client.get("/api/v1/analytics/breakdown")
        assert res.status_code == 200
        data = res.json()["data"]
        assert "total_active_jobs" in data
        assert data["total_active_jobs"] >= 2
        assert "by_employment_type" in data
        assert "by_experience_level" in data

        emp_types = [item["employment_type"] for item in data["by_employment_type"]]
        assert "full_time" in emp_types

        exp_levels = [item["experience_level"] for item in data["by_experience_level"]]
        assert "mid" in exp_levels or "senior" in exp_levels
