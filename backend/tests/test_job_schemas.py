"""Unit tests for Job Pydantic validation schemas."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.schemas.enums import EmploymentType, ExperienceLevel, SourcePlatform
from app.schemas.job import JobCreate, JobRead, JobUpdate


class TestJobSchemas:
    """Test suite for core Job validation schemas."""

    def test_valid_job_create(self) -> None:
        payload = {
            "title": "Backend Python Engineer",
            "company_name": "Tech Corp",
            "location": "San Francisco, CA",
            "is_remote": True,
            "employment_type": "full_time",
            "experience_level": "senior",
            "min_salary": 120000.0,
            "max_salary": 160000.0,
            "salary_currency": "USD",
            "description": "Design and build scalable APIs using FastAPI and PostgreSQL.",
            "requirements_raw": "Python, FastAPI, SQL",
            "source_platform": "linkedin",
        }
        job = JobCreate(**payload)
        assert job.title == "Backend Python Engineer"
        assert job.is_remote is True
        assert job.employment_type == EmploymentType.FULL_TIME
        assert job.experience_level == ExperienceLevel.SENIOR
        assert job.source_platform == SourcePlatform.LINKEDIN

    def test_job_create_minimal_defaults(self) -> None:
        payload = {
            "title": "Junior Developer",
            "company_name": "Startup Inc",
            "description": "Entry-level software engineering role.",
        }
        job = JobCreate(**payload)
        assert job.employment_type == EmploymentType.FULL_TIME
        assert job.experience_level == ExperienceLevel.MID
        assert job.salary_currency == "USD"
        assert job.is_remote is False
        assert job.is_active is True

    def test_job_create_validation_errors(self) -> None:
        # Title too short
        with pytest.raises(ValidationError):
            JobCreate(title="A", company_name="Co", description="A valid long description here.")

        # Company empty
        with pytest.raises(ValidationError):
            JobCreate(title="Engineer", company_name="", description="A valid long description here.")

        # Description too short
        with pytest.raises(ValidationError):
            JobCreate(title="Engineer", company_name="Co", description="Short")

    def test_job_update_partial(self) -> None:
        update = JobUpdate(title="Staff Engineer", is_remote=True)
        assert update.title == "Staff Engineer"
        assert update.is_remote is True
        assert update.company_name is None
        assert update.min_salary is None

    def test_job_read_serialization(self) -> None:
        now = datetime.now(timezone.utc)
        payload = {
            "id": 1,
            "title": "Data Engineer",
            "company_name": "DataWorks",
            "location": "Remote",
            "is_remote": True,
            "employment_type": "contract",
            "experience_level": "lead",
            "min_salary": 140000.0,
            "max_salary": 180000.0,
            "salary_currency": "USD",
            "description": "Build high throughput ETL pipelines.",
            "requirements_raw": None,
            "source_url": "https://example.com/jobs/1",
            "source_platform": "manual",
            "is_active": True,
            "posted_date": now,
            "created_at": now,
            "updated_at": now,
        }
        job = JobRead(**payload)
        assert job.id == 1
        assert job.title == "Data Engineer"
        assert job.created_at == now

    def test_salary_currency_normalization(self) -> None:
        job = JobCreate(
            title="DevOps Engineer",
            company_name="Cloud Solutions",
            description="Manage CI/CD pipelines.",
            salary_currency="  eur  ",
        )
        assert job.salary_currency == "EUR"

    def test_invalid_salary_currency_raises(self) -> None:
        with pytest.raises(ValidationError):
            JobCreate(
                title="DevOps Engineer",
                company_name="Cloud Solutions",
                description="Manage CI/CD pipelines.",
                salary_currency="INVALID_LONG",
            )

    def test_inverted_salary_range_raises(self) -> None:
        with pytest.raises(ValidationError) as exc:
            JobCreate(
                title="DevOps Engineer",
                company_name="Cloud Solutions",
                description="Manage CI/CD pipelines.",
                min_salary=150000.0,
                max_salary=100000.0,
            )
        assert "min_salary cannot be greater than max_salary" in str(exc.value)

    def test_equal_salary_range_is_valid(self) -> None:
        job = JobCreate(
            title="DevOps Engineer",
            company_name="Cloud Solutions",
            description="Manage CI/CD pipelines.",
            min_salary=100000.0,
            max_salary=100000.0,
        )
        assert job.min_salary == 100000.0
        assert job.max_salary == 100000.0

    def test_negative_salary_raises(self) -> None:
        with pytest.raises(ValidationError):
            JobCreate(
                title="DevOps Engineer",
                company_name="Cloud Solutions",
                description="Manage CI/CD pipelines.",
                min_salary=-500.0,
            )

    def test_job_update_salary_range_validation(self) -> None:
        # Valid update
        update = JobUpdate(min_salary=80000.0, max_salary=120000.0)
        assert update.min_salary == 80000.0

        # Inverted update raises
        with pytest.raises(ValidationError):
            JobUpdate(min_salary=150000.0, max_salary=100000.0)
