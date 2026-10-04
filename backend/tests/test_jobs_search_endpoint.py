"""Tests for GET /jobs/search endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.job import JobPosting


class TestJobsSearchEndpoint:

    def test_search_jobs_by_keyword(self, client: TestClient) -> None:
        tag = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            job1 = JobPosting(
                title=f"Senior Cloud Architect {tag}",
                company_name=f"TechCorp {tag}",
                location="Seattle, WA",
                is_remote=True,
                employment_type="full_time",
                experience_level="senior",
                description="Lead cloud infrastructure design",
                is_active=True,
            )
            job2 = JobPosting(
                title=f"Junior Frontend Developer {tag}",
                company_name=f"WebCorp {tag}",
                location="Austin, TX",
                is_remote=False,
                employment_type="full_time",
                experience_level="entry",
                description="React and CSS developer",
                is_active=True,
            )
            db.add_all([job1, job2])
            db.commit()

        # Search for Cloud Architect
        res = client.get(f"/api/v1/jobs/search?q=Cloud%20Architect%20{tag}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["pagination"]["total_items"] >= 1
        titles = [item["title"] for item in data["items"]]
        assert any(f"Senior Cloud Architect {tag}" in t for t in titles)

    def test_search_jobs_with_location_filter(self, client: TestClient) -> None:
        tag = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            job = JobPosting(
                title=f"Golang Engineer {tag}",
                company_name=f"GoInc {tag}",
                location=f"Chicago_{tag}",
                is_remote=False,
                employment_type="full_time",
                experience_level="mid",
                description="Golang microservices backend",
                is_active=True,
            )
            db.add(job)
            db.commit()

        res = client.get(f"/api/v1/jobs/search?q=Golang&location=Chicago_{tag}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["pagination"]["total_items"] == 1
        assert data["items"][0]["location"] == f"Chicago_{tag}"
