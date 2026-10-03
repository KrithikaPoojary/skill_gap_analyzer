"""Tests for job posting engagement statistics endpoint."""

import pytest
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.job import JobPosting
from app.models.saved_job import ApplicationStatus, UserSavedJob
from app.models.user import User


def test_get_job_stats_not_found(client: TestClient) -> None:
    """Non-existent job returns 404."""
    response = client.get("/api/v1/jobs/999999/stats")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False


def test_get_job_stats_empty(client: TestClient) -> None:
    """Existing job with no bookmarks returns zero stats."""
    with SessionLocal() as db:
        job = JobPosting(
            title="Software Engineer",
            company_name="TechCorp",
            description="Write clean code",
            min_salary=80000,
            max_salary=120000,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

    response = client.get(f"/api/v1/jobs/{job_id}/stats")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["job_id"] == job_id
    assert data["total_saved"] == 0
    assert data["application_count"] == 0


def test_get_job_stats_with_applications(client: TestClient) -> None:
    """Job with bookmarks and applications aggregates correctly."""
    with SessionLocal() as db:
        u1 = User(email="applicant1@test.com", hashed_password="pw", full_name="User 1")
        u2 = User(email="applicant2@test.com", hashed_password="pw", full_name="User 2")
        db.add_all([u1, u2])
        db.commit()
        db.refresh(u1)
        db.refresh(u2)

        job = JobPosting(
            title="Backend Engineer",
            company_name="DataCorp",
            description="Build Python services",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = job.id

        s1 = UserSavedJob(user_id=u1.id, job_id=job.id, status=ApplicationStatus.SAVED)
        s2 = UserSavedJob(user_id=u2.id, job_id=job.id, status=ApplicationStatus.APPLIED)
        db.add_all([s1, s2])
        db.commit()

    response = client.get(f"/api/v1/jobs/{job_id}/stats")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["job_id"] == job_id
    assert data["total_saved"] == 2
    assert data["application_count"] == 1
    assert data["status_breakdown"]["saved"] == 1
    assert data["status_breakdown"]["applied"] == 1
