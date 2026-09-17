"""Pydantic schemas for career role recommendations."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class MissingSkillDetail(BaseModel):
    """Missing skill with importance weight."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    weight: float


class RoleRecommendationItem(BaseModel):
    """Ranked career role recommendation item."""

    model_config = ConfigDict(from_attributes=True)

    role_id: int
    title: str
    slug: str
    category: str
    min_experience_years: float = 1.0
    match_score: float = Field(..., ge=0.0, le=1.0, description="Weighted fit score [0.0, 1.0]")
    coverage_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of required skills met")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[MissingSkillDetail] = Field(default_factory=list)
    missing_critical: list[str] = Field(default_factory=list)


class RecommendationsForSkillsRequest(BaseModel):
    """Request payload to compute role recommendations from a list of skills."""

    skills: list[str] = Field(..., min_length=1, description="List of candidate skills")
    limit: int = Field(5, ge=1, le=50, description="Max recommendations to return")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum match score filter")
    category: str | None = Field(None, description="Optional role category filter")


class RecommendationsForTextRequest(BaseModel):
    """Request payload to extract skills from text and compute recommendations."""

    text: str = Field(..., min_length=3, description="Resume or profile unstructured text")
    limit: int = Field(5, ge=1, le=50, description="Max recommendations to return")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum match score filter")
    category: str | None = Field(None, description="Optional role category filter")
    min_confidence: float = Field(0.60, ge=0.0, le=1.0, description="Minimum skill extraction confidence")


class RecommendationsResponse(BaseModel):
    """Response containing ranked role recommendations."""

    model_config = ConfigDict(from_attributes=True)

    recommendations: list[RoleRecommendationItem] = Field(default_factory=list)


class TextRecommendationsResponse(BaseModel):
    """Response containing extracted skills and ranked recommendations."""

    model_config = ConfigDict(from_attributes=True)

    extracted_skills: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[RoleRecommendationItem] = Field(default_factory=list)
