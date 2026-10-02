"""Pydantic schemas for skill gap analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class GapAnalysisSkillsRequest(BaseModel):
    """Request payload to analyse skill gaps from a list of skills."""

    skills: list[str] = Field(..., min_length=1, description="Candidate skills")
    role_id: int | None = Field(None, description="Target role ID")
    role_name: str | None = Field(None, description="Target role name / title")
    role_slug: str | None = Field(None, description="Target role slug")


class GapAnalysisTextRequest(BaseModel):
    """Request payload to extract skills from text and analyse gap."""

    text: str = Field(..., min_length=3, description="Resume or profile text")
    role_id: int | None = Field(None, description="Target role ID")
    role_name: str | None = Field(None, description="Target role name / title")
    role_slug: str | None = Field(None, description="Target role slug")
    min_confidence: float = Field(0.60, ge=0.0, le=1.0, description="Minimum extraction confidence")


class GapReportSchema(BaseModel):
    """Schema representing gap analysis results."""

    model_config = ConfigDict(from_attributes=True)

    role_name: str
    role_id: int | None = None
    category: str | None = None
    min_experience_years: float | None = None
    gap_score: float
    weighted_gap_score: float
    coverage_pct: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[dict[str, Any]] = Field(default_factory=list)
    surplus_skills: list[str] = Field(default_factory=list)
    missing_critical: list[str] = Field(default_factory=list)


class GapAnalysisTextResponse(BaseModel):
    """Response containing extracted skills and gap report."""

    model_config = ConfigDict(from_attributes=True)

    extracted_skills: list[dict[str, Any]] = Field(default_factory=list)
    gap_report: GapReportSchema


class GapSnapshotRead(BaseModel):
    """Schema for historical gap analysis record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role_id: int | None = None
    role_title: str
    readiness_score: float
    matched_skills: list[Any] = Field(default_factory=list)
    missing_skills: list[Any] = Field(default_factory=list)
    created_at: datetime | None = None


class CompareRolesRequest(BaseModel):
    """Request payload to compare multiple target roles."""

    roles: list[str] = Field(..., min_length=2, max_length=10, description="List of role titles or keywords to compare")
    skills: list[str] | None = Field(default=None, description="Optional explicit skills list; if omitted in /me, user profile is used")

