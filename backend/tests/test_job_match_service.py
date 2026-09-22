"""Unit tests for JobMatchService."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill
from app.models.user import Profile, User
from app.schemas.job_match import JobMatchCriteria
from app.services.job_match_service import job_match_service


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed skills
    s_py = Skill(name="Python", normalized_name="python")
    s_fast = Skill(name="FastAPI", normalized_name="fastapi")
    s_sql = Skill(name="PostgreSQL", normalized_name="postgresql")
    session.add_all([s_py, s_fast, s_sql])
    session.flush()

    # Seed job 1 (strong match)
    job1 = JobPosting(
        title="Python Engineer",
        company_name="Alpha Co",
        location="Remote",
        is_remote=True,
        employment_type="full_time",
        experience_level="mid",
        min_salary=90000,
        max_salary=120000,
        description="FastAPI microservices role.",
        is_active=True,
    )
    # Seed job 2 (poor match)
    job2 = JobPosting(
        title="Frontend Dev",
        company_name="Beta Co",
        location="New York, NY",
        is_remote=False,
        employment_type="full_time",
        experience_level="senior",
        min_salary=140000,
        max_salary=180000,
        description="React and TypeScript role.",
        is_active=True,
    )
    session.add_all([job1, job2])
    session.flush()

    # Add skills to job1
    js1 = JobSkill(job_id=job1.id, skill_id=s_py.id, is_required=True, importance_weight=1.0)
    js2 = JobSkill(job_id=job1.id, skill_id=s_fast.id, is_required=True, importance_weight=1.0)
    # Add skills to job2
    js3 = JobSkill(job_id=job2.id, skill_id=s_sql.id, is_required=False, importance_weight=0.5)
    session.add_all([js1, js2, js3])
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_match_jobs_ranked_correctly(db_session):
    criteria = JobMatchCriteria(
        skills=["Python", "FastAPI"],
        years_of_experience=3.0,
        location="Remote",
        prefers_remote=True,
    )
    response = job_match_service.match_jobs(db_session, criteria)
    assert response.total == 2
    # Alpha Co (Python Engineer) should be ranked 1st
    top_match = response.items[0]
    assert top_match.title == "Python Engineer"
    assert top_match.match_detail.composite_score > 80.0
    assert "Python" in top_match.match_detail.matched_skills


def test_match_single_job(db_session):
    detail = job_match_service.match_single_job(
        db_session,
        job_id=1,
        candidate_skills=["Python", "FastAPI"],
        candidate_years=3.0,
    )
    assert detail is not None
    assert detail.composite_score > 70.0
    assert len(detail.missing_required_skills) == 0
