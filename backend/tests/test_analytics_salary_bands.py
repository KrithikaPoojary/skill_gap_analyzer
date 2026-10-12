"""Tests for salary bands analytics endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient
from app.db.session import SessionLocal
from app.models.job import JobPosting


class TestAnalyticsSalaryBands:
    """Tests for GET /api/v1/analytics/salary-bands."""

    def test_salary_bands_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analytics/salary-bands")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["success"] is True
        data = payload["data"]
        assert "currency" in data
        assert "bands" in data
        assert "total_jobs_with_salary" in data
        assert isinstance(data["bands"], list)

    def test_salary_bands_calculation(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            j1 = JobPosting(
                title=f"Senior Python {suffix}",
                company_name=f"Comp {suffix}",
                description="desc",
                experience_level="senior",
                min_salary=120000.0,
                max_salary=160000.0,
                salary_currency="USD",
            )
            j2 = JobPosting(
                title=f"Staff Python {suffix}",
                company_name=f"Comp {suffix}",
                description="desc",
                experience_level="senior",
                min_salary=140000.0,
                max_salary=180000.0,
                salary_currency="USD",
            )
            db.add_all([j1, j2])
            db.commit()

        resp = client.get("/api/v1/analytics/salary-bands?currency=USD")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_jobs_with_salary"] >= 2

        senior_band = next((b for b in data["bands"] if b["experience_level"] == "senior"), None)
        assert senior_band is not None
        assert senior_band["job_count"] >= 2
        assert senior_band["avg_min_salary"] > 0
        assert senior_band["highest_salary"] >= 180000.0
        assert senior_band["midpoint_salary"] is not None

