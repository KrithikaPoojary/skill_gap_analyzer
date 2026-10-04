"""Tests for GET /jobs/{job_id}/saved endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.job import JobPosting


class TestCheckJobSaved:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"savecheck_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_check_job_saved_flow(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        tag = uuid.uuid4().hex[:6]

        with SessionLocal() as db:
            job = JobPosting(
                title=f"Site Reliability Engineer {tag}",
                company_name=f"SRECorp {tag}",
                location="Remote",
                is_remote=True,
                employment_type="full_time",
                experience_level="senior",
                description="K8s and Terraform SRE",
                is_active=True,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            job_id = job.id

        # 1. Before saving -> is_saved is False
        res0 = client.get(f"/api/v1/jobs/{job_id}/saved", headers=headers)
        assert res0.status_code == 200
        assert res0.json()["data"]["is_saved"] is False

        # 2. Save job
        res_save = client.post(
            f"/api/v1/jobs/{job_id}/save",
            json={"notes": "Top choice company"},
            headers=headers,
        )
        assert res_save.status_code == 201

        # 3. Check again -> is_saved is True
        res1 = client.get(f"/api/v1/jobs/{job_id}/saved", headers=headers)
        assert res1.status_code == 200
        assert res1.json()["data"]["is_saved"] is True
        assert res1.json()["data"]["status"] == "saved"
        assert res1.json()["data"]["notes"] == "Top choice company"
