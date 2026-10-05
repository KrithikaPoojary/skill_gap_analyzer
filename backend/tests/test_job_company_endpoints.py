"""Tests for GET /jobs/companies and GET /jobs/company/{company_name} endpoints."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import engine
from app.models.job import JobPosting
from sqlalchemy.orm import Session


class TestJobCompanyEndpoints:

    def _create_jobs(self, company_name: str, count: int = 2) -> list[int]:
        """Helper to seed job postings for a company."""
        uid = uuid.uuid4().hex[:6]
        ids = []
        with Session(engine) as db:
            for i in range(count):
                job = JobPosting(
                    title=f"Engineer {i} {uid}",
                    company_name=company_name,
                    location="Remote",
                    description="Job description",
                    is_active=True,
                    is_remote=True,
                )
                db.add(job)
                db.commit()
                ids.append(job.id)
        return ids

    def test_list_companies_returns_list(self, client: TestClient) -> None:
        uid = uuid.uuid4().hex[:6]
        company = f"TechCorp {uid}"
        self._create_jobs(company, count=2)

        res = client.get("/api/v1/jobs/companies")
        assert res.status_code == 200
        data = res.json()["data"]
        assert "companies" in data
        assert isinstance(data["companies"], list)
        company_names = [c["company_name"] for c in data["companies"]]
        assert company in company_names

    def test_list_companies_has_job_counts(self, client: TestClient) -> None:
        uid = uuid.uuid4().hex[:6]
        company = f"DataCorp {uid}"
        self._create_jobs(company, count=3)

        res = client.get("/api/v1/jobs/companies")
        data = res.json()["data"]["companies"]
        match = next((c for c in data if c["company_name"] == company), None)
        assert match is not None
        assert match["job_count"] == 3

    def test_get_jobs_by_company_returns_filtered(self, client: TestClient) -> None:
        uid = uuid.uuid4().hex[:6]
        company = f"FilterCorp {uid}"
        self._create_jobs(company, count=2)

        res = client.get(f"/api/v1/jobs/company/{company}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["company_name"] == company
        assert data["total"] == 2
        for j in data["jobs"]:
            assert company in j["company_name"]

    def test_get_jobs_by_company_no_results(self, client: TestClient) -> None:
        res = client.get("/api/v1/jobs/company/NonExistentCompanyXYZ12345")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] == 0
        assert data["jobs"] == []
