"""Tests for candidate saved jobs pipeline analytics endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.job import JobPosting
from app.models.saved_job import ApplicationStatus, UserSavedJob


class TestSavedJobsPipelineStatsEndpoint:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        email = f"pipestats_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/jobs/saved/stats")
        assert resp.status_code == 401

    def test_empty_pipeline_stats(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        resp = client.get(
            "/api/v1/jobs/saved/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_tracked_jobs"] == 0
        assert data["application_rate"] == 0.0
        assert data["interview_rate"] == 0.0

    def test_pipeline_stats_with_applications(self, client: TestClient) -> None:
        uid, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Seed 3 job postings and save them under different stages
        with SessionLocal() as db:
            j1 = JobPosting(title="Dev 1", company_name="Company A", description="Desc")
            j2 = JobPosting(title="Dev 2", company_name="Company B", description="Desc")
            j3 = JobPosting(title="Dev 3", company_name="Company C", description="Desc")
            db.add_all([j1, j2, j3])
            db.commit()
            db.refresh(j1)
            db.refresh(j2)
            db.refresh(j3)

            # 1 saved, 1 applied, 1 interviewing
            s1 = UserSavedJob(user_id=uid, job_id=j1.id, status=ApplicationStatus.SAVED)
            s2 = UserSavedJob(user_id=uid, job_id=j2.id, status=ApplicationStatus.APPLIED)
            s3 = UserSavedJob(user_id=uid, job_id=j3.id, status=ApplicationStatus.INTERVIEWING)
            db.add_all([s1, s2, s3])
            db.commit()

        resp = client.get(
            "/api/v1/jobs/saved/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_tracked_jobs"] == 3
        assert data["saved"] == 1
        assert data["applied"] == 1
        assert data["interviewing"] == 1
        assert data["active_applications"] == 2
        assert data["total_advanced"] == 2
        assert data["application_rate"] == 66.67
        assert data["interview_rate"] == 50.0
