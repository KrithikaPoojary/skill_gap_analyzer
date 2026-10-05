"""Tests for clearing bookmarked jobs endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.job import JobPosting
from app.models.saved_job import ApplicationStatus, UserSavedJob


class TestClearSavedJobs:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"clear_jobs_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_clear_all_and_filtered_saved_jobs(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Create two jobs and bookmarks
        suffix = uuid.uuid4().hex[:6]
        with SessionLocal() as db:
            j1 = JobPosting(title=f"Engineer 1 {suffix}", company_name="Co1", description="desc")
            j2 = JobPosting(title=f"Engineer 2 {suffix}", company_name="Co2", description="desc")
            db.add_all([j1, j2])
            db.commit()
            db.refresh(j1)
            db.refresh(j2)

            # User saves j1 as SAVED and j2 as APPLIED
            sj1 = UserSavedJob(user_id=user_id, job_id=j1.id, status=ApplicationStatus.SAVED)
            sj2 = UserSavedJob(user_id=user_id, job_id=j2.id, status=ApplicationStatus.APPLIED)
            db.add_all([sj1, sj2])
            db.commit()

        # Delete with status filter=saved
        del_saved = client.delete("/api/v1/jobs/saved/clear?status=saved", headers=headers)
        assert del_saved.status_code == 200
        assert del_saved.json()["data"]["cleared_count"] == 1

        # Check remaining
        list_resp = client.get("/api/v1/jobs/saved", headers=headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["data"]["total"] == 1

        # Clear all remaining
        clear_all = client.delete("/api/v1/jobs/saved/clear", headers=headers)
        assert clear_all.status_code == 200
        assert clear_all.json()["data"]["cleared_count"] == 1

        # Verify completely empty
        empty_list = client.get("/api/v1/jobs/saved", headers=headers)
        assert empty_list.status_code == 200
        assert empty_list.json()["data"]["total"] == 0
