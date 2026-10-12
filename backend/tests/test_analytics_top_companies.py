"""Tests for top hiring companies analytics endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient
from app.db.session import SessionLocal
from app.models.job import JobPosting


class TestAnalyticsTopCompanies:
    """Tests for GET /api/v1/analytics/companies/top."""

    def test_top_companies_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analytics/companies/top")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["success"] is True
        data = payload["data"]
        assert "companies" in data
        assert "total_companies" in data
        assert isinstance(data["companies"], list)

    def test_top_companies_with_limit(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analytics/companies/top?limit=2")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["companies"]) <= 2

    def test_top_companies_ranking_and_metrics(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        company_alpha = f"AlphaCorp {suffix}"
        company_beta = f"BetaCorp {suffix}"

        with SessionLocal() as db:
            j1 = JobPosting(
                title=f"SWE 1 {suffix}",
                company_name=company_alpha,
                description="desc",
                is_remote=True,
            )
            j2 = JobPosting(
                title=f"SWE 2 {suffix}",
                company_name=company_alpha,
                description="desc",
                is_remote=False,
            )
            j3 = JobPosting(
                title=f"SWE 3 {suffix}",
                company_name=company_beta,
                description="desc",
                is_remote=True,
            )
            db.add_all([j1, j2, j3])
            db.commit()

        resp = client.get("/api/v1/analytics/companies/top?limit=50")
        assert resp.status_code == 200
        data = resp.json()["data"]
        comps = {c["company_name"]: c for c in data["companies"]}

        assert company_alpha in comps
        assert comps[company_alpha]["total_jobs"] >= 2
        assert comps[company_alpha]["remote_jobs"] >= 1
        assert "remote_percentage" in comps[company_alpha]
