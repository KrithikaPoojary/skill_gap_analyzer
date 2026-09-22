"""Pydantic schemas for quantitative job matching and application tracking."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class JobMatchCriteria(BaseModel):
    """Input criteria for querying matching jobs."""

    skills: list[str] = Field(
        ...,
        min_length=1,
        description="Candidate's current technical competencies.",
        examples=[["Python", "FastAPI", "PostgreSQL", "Docker"]],
    )
    years_of_experience: float | None = Field(
        None,
        ge=0.0,
        le=50.0,
        description="Candidate's total professional experience in years.",
    )
    desired_salary: float | None = Field(
        None,
        ge=0.0,
        description="Candidate's minimum or target annual base salary.",
    )
    location: str | None = Field(
        None,
        description="Candidate's preferred location (city, state, or country).",
    )
    prefers_remote: bool | None = Field(
        None,
        description="Whether candidate strictly seeks remote roles.",
    )
    min_match_score: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Minimum composite match score threshold to include in results.",
    )


class JobMatchScoreDetail(BaseModel):
    """Multi-factor score breakdown for a specific job."""

    skill_score: float = Field(..., ge=0.0, le=100.0)
    experience_score: float = Field(..., ge=0.0, le=100.0)
    location_score: float = Field(..., ge=0.0, le=100.0)
    salary_score: float = Field(..., ge=0.0, le=100.0)
    composite_score: float = Field(..., ge=0.0, le=100.0)
    match_tier: str = Field(..., description="Categorical rating: Strong, Moderate, Low")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)


class JobMatchResult(BaseModel):
    """Summarized job posting details paired with match metrics."""

    job_id: int
    title: str
    company_name: str
    location: str | None
    is_remote: bool
    employment_type: str
    experience_level: str
    min_salary: float | None
    max_salary: float | None
    currency: str
    posted_date: datetime | None
    match_detail: JobMatchScoreDetail


class PaginatedJobMatchResponse(BaseModel):
    """Paginated collection of ranked job matches."""

    items: list[JobMatchResult]
    total: int
    offset: int
    limit: int
