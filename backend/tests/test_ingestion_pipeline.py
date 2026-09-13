"""Integration tests for the dataset ingestion pipeline service."""

import csv
import json
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill
from app.services.ingestion_service import IngestionService


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def ingestion_service():
    return IngestionService()


class TestIngestionPipeline:
    """Test suite for batch data ingestion, deduplication, and skill linkage."""

    SAMPLE_RECORDS = [
        {
            "title": "Backend Python Engineer",
            "company_name": "Datadog",
            "location": "New York, NY",
            "is_remote": True,
            "employment_type": "full_time",
            "experience_level": "senior",
            "min_salary": 130000.0,
            "max_salary": 180000.0,
            "salary_currency": "USD",
            "description": "Building high-performance telemetry and logging backend APIs.",
            "skills": [
                {"name": "Python", "is_required": True, "importance_weight": 1.5},
                {"name": "FastAPI", "is_required": True, "importance_weight": 1.2},
                {"name": "k8s", "is_required": False, "importance_weight": 0.8},
            ],
        },
        {
            "title": "Frontend React Developer",
            "company_name": "Shopify",
            "location": "Remote",
            "is_remote": True,
            "employment_type": "full_time",
            "experience_level": "mid",
            "min_salary": 95000.0,
            "max_salary": 140000.0,
            "salary_currency": "USD",
            "description": "Crafting merchant dashboard user experiences with React and TypeScript.",
            "skills": [
                {"name": "React", "is_required": True, "importance_weight": 1.8},
                {"name": "TypeScript", "is_required": True, "importance_weight": 1.5},
            ],
        },
    ]

    def test_ingest_records_persists_to_db(self, db_session, ingestion_service) -> None:
        report = ingestion_service.ingest_records(db_session, self.SAMPLE_RECORDS)

        assert report.total_records == 2
        assert report.inserted_records == 2
        assert report.skipped_records == 0
        assert report.error_records == 0

        # Verify JobPosting persistence
        jobs = db_session.query(JobPosting).all()
        assert len(jobs) == 2

        # Verify skill resolution and association
        datadog_job = db_session.query(JobPosting).filter_by(company_name="Datadog").first()
        assert datadog_job is not None
        assert len(datadog_job.job_skills) == 3

        # Verify alias normalization: 'k8s' should resolve to 'Kubernetes'
        k8s_skill = db_session.query(Skill).filter_by(name="Kubernetes").first()
        assert k8s_skill is not None

    def test_ingest_deduplication(self, db_session, ingestion_service) -> None:
        # First ingestion
        ingestion_service.ingest_records(db_session, self.SAMPLE_RECORDS)
        assert db_session.query(JobPosting).count() == 2

        # Second ingestion of the same records
        second_report = ingestion_service.ingest_records(db_session, self.SAMPLE_RECORDS)
        assert second_report.inserted_records == 0
        assert second_report.skipped_records == 2
        assert db_session.query(JobPosting).count() == 2

    def test_dry_run_leaves_database_empty(self, db_session, ingestion_service) -> None:
        report = ingestion_service.ingest_records(db_session, self.SAMPLE_RECORDS, dry_run=True)

        assert report.inserted_records == 2
        assert report.total_records == 2
        # Ensure nothing was actually written to DB
        assert db_session.query(JobPosting).count() == 0
        assert db_session.query(Skill).count() == 0

    def test_ingest_handles_malformed_record(self, db_session, ingestion_service) -> None:
        records = [
            {
                "title": "",  # Empty title should fail
                "company_name": "NoTitle Corp",
                "description": "Invalid job without title",
            },
            {
                "title": "Valid SRE",
                "company_name": "Cloudflare",
                "description": "Reliable distributed systems infrastructure.",
            },
        ]
        report = ingestion_service.ingest_records(db_session, records)

        assert report.total_records == 2
        assert report.inserted_records == 1
        assert report.error_records == 1
        assert len(report.errors) == 1

    def test_salary_swapping_when_inverted(self, db_session, ingestion_service) -> None:
        inverted_record = [
            {
                "title": "Senior Data Architect",
                "company_name": "Snowflake",
                "min_salary": 200000.0,
                "max_salary": 150000.0,  # Inverted
                "description": "Designing next-generation analytics architectures.",
            }
        ]
        report = ingestion_service.ingest_records(db_session, inverted_record)
        assert report.inserted_records == 1

        job = db_session.query(JobPosting).filter_by(company_name="Snowflake").first()
        assert job.min_salary == 150000.0
        assert job.max_salary == 200000.0

    def test_ingest_csv_file(self, db_session, ingestion_service, tmp_path) -> None:
        csv_file = tmp_path / "test_jobs.csv"
        rows = [
            {
                "title": "Lead DevOps Engineer",
                "company_name": "HashiCorp",
                "location": "Austin, TX",
                "is_remote": "True",
                "employment_type": "full_time",
                "experience_level": "lead",
                "min_salary": "160000",
                "max_salary": "220000",
                "salary_currency": "USD",
                "description": "Managing enterprise Terraform cloud infrastructure.",
                "skills_str": "Terraform, Docker, AWS, Python",
            }
        ]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        report = ingestion_service.ingest_csv_file(db_session, str(csv_file))
        assert report.total_records == 1
        assert report.inserted_records == 1

        job = db_session.query(JobPosting).filter_by(company_name="HashiCorp").first()
        assert job is not None
        assert len(job.job_skills) == 4
