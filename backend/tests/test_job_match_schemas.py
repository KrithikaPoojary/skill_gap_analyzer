"""Unit tests for JobMatch Pydantic schemas."""

from datetime import datetime
import pytest
from pydantic import ValidationError
from app.schemas.job_match import (
    JobMatchCriteria,
    JobMatchResult,
    JobMatchScoreDetail,
    PaginatedJobMatchResponse,
)


def test_job_match_criteria_valid():
    criteria = JobMatchCriteria(
        skills=["Python", "FastAPI"],
        years_of_experience=4.5,
        desired_salary=120000,
        location="Austin, TX",
        prefers_remote=True,
        min_match_score=60.0,
    )
    assert criteria.skills == ["Python", "FastAPI"]
    assert criteria.years_of_experience == 4.5
    assert criteria.min_match_score == 60.0


def test_job_match_criteria_empty_skills_fails():
    with pytest.raises(ValidationError):
        JobMatchCriteria(skills=[])


def test_job_match_score_detail_valid():
    detail = JobMatchScoreDetail(
        skill_score=85.0,
        experience_score=100.0,
        location_score=90.0,
        salary_score=80.0,
        composite_score=87.5,
        match_tier="Strong",
        matched_skills=["Python", "FastAPI"],
        missing_skills=["Docker"],
        missing_required_skills=[],
    )
    assert detail.composite_score == 87.5
    assert detail.match_tier == "Strong"


def test_job_match_result_and_pagination():
    detail = JobMatchScoreDetail(
        skill_score=80.0,
        experience_score=80.0,
        location_score=100.0,
        salary_score=80.0,
        composite_score=82.0,
        match_tier="Strong",
    )
    result = JobMatchResult(
        job_id=1,
        title="Backend Engineer",
        company_name="Acme Tech",
        location="Remote",
        is_remote=True,
        employment_type="full_time",
        experience_level="mid",
        min_salary=90000,
        max_salary=130000,
        currency="USD",
        posted_date=datetime.now(),
        match_detail=detail,
    )
    assert result.job_id == 1
    assert result.company_name == "Acme Tech"

    paginated = PaginatedJobMatchResponse(items=[result], total=1, offset=0, limit=10)
    assert len(paginated.items) == 1
    assert paginated.total == 1
