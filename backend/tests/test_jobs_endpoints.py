"""Integration tests for the /api/v1/jobs REST API endpoints."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.api.deps import get_db
from app.db.base import Base
import app.models  # noqa: F401
from app.main import create_application


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def api_client(db_session: Session) -> TestClient:
    app = create_application()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client


class TestJobsEndpoints:
    """Integration tests for jobs CRUD API endpoints."""

    JOB_PAYLOAD = {
        "title": "Senior Python Engineer",
        "company_name": "Acme Corp",
        "description": "Building distributed backend APIs using Python and FastAPI.",
        "is_remote": True,
        "employment_type": "full_time",
        "experience_level": "senior",
        "min_salary": 120000.0,
        "max_salary": 180000.0,
        "salary_currency": "USD",
    }

    def test_create_job_returns_201(self, api_client: TestClient) -> None:
        response = api_client.post("/api/v1/jobs", json=self.JOB_PAYLOAD)
        assert response.status_code == 201

    def test_create_job_response_structure(self, api_client: TestClient) -> None:
        response = api_client.post("/api/v1/jobs", json=self.JOB_PAYLOAD)
        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert data["title"] == self.JOB_PAYLOAD["title"]
        assert data["company_name"] == self.JOB_PAYLOAD["company_name"]
        assert data["is_remote"] is True
        assert "id" in data

    def test_create_job_invalid_salary_range(self, api_client: TestClient) -> None:
        bad_payload = {**self.JOB_PAYLOAD, "min_salary": 200000.0, "max_salary": 100000.0}
        response = api_client.post("/api/v1/jobs", json=bad_payload)
        assert response.status_code == 422

    def test_list_jobs_endpoint(self, api_client: TestClient) -> None:
        api_client.post("/api/v1/jobs", json=self.JOB_PAYLOAD)
        response = api_client.get("/api/v1/jobs")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "items" in body["data"]
        assert "pagination" in body["data"]

    def test_get_job_by_id(self, api_client: TestClient) -> None:
        create_resp = api_client.post("/api/v1/jobs", json=self.JOB_PAYLOAD)
        job_id = create_resp.json()["data"]["id"]

        get_resp = api_client.get(f"/api/v1/jobs/{job_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()["data"]
        assert data["id"] == job_id

    def test_get_nonexistent_job_returns_404(self, api_client: TestClient) -> None:
        response = api_client.get("/api/v1/jobs/999999")
        assert response.status_code == 404

    def test_update_job_title(self, api_client: TestClient) -> None:
        create_resp = api_client.post("/api/v1/jobs", json=self.JOB_PAYLOAD)
        job_id = create_resp.json()["data"]["id"]

        update_resp = api_client.patch(f"/api/v1/jobs/{job_id}", json={"title": "Lead Python Engineer"})
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["title"] == "Lead Python Engineer"

    def test_delete_job_soft_deletes(self, api_client: TestClient) -> None:
        create_resp = api_client.post("/api/v1/jobs", json=self.JOB_PAYLOAD)
        job_id = create_resp.json()["data"]["id"]

        del_resp = api_client.delete(f"/api/v1/jobs/{job_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["data"]["is_active"] is False
