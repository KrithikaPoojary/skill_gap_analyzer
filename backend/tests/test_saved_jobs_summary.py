"""Tests for GET /jobs/saved/summary endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.models.job import JobPosting
from app.models.saved_job import ApplicationStatus, UserSavedJob
from sqlalchemy.orm import Session


class TestSavedJobsSummary:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"save_sum_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_saved_summary_empty(self, client: TestClient) -> None:
        _, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/v1/jobs/saved/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_tracked_jobs"] == 0
        assert data["saved"] == 0
        assert data["applied"] == 0

    def test_saved_summary_with_jobs(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        with Session(engine) as db:
            uid = uuid.uuid4().hex[:6]
            j1 = JobPosting(title=f"Job 1 {uid}", company_name=f"Comp {uid}", description="d", is_active=True)
            j2 = JobPosting(title=f"Job 2 {uid}", company_name=f"Comp {uid}", description="d", is_active=True)
            db.add_all([j1, j2])
            db.flush()

            s1 = UserSavedJob(user_id=user_id, job_id=j1.id, status=ApplicationStatus.SAVED)
            s2 = UserSavedJob(user_id=user_id, job_id=j2.id, status=ApplicationStatus.APPLIED)
            db.add_all([s1, s2])
            db.commit()

        res = client.get("/api/v1/jobs/saved/summary", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_tracked_jobs"] == 2
        assert data["saved"] == 1
        assert data["applied"] == 1
        assert "status_breakdown" in data
