"""Pydantic schemas and DTOs for market analytics reporting."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DistributionStatsSchema(BaseModel):
    """Statistical summary schema for numerical metrics."""

    model_config = ConfigDict(from_attributes=True)

    count: int = Field(..., description="Number of observations")
    mean: float | None = Field(None, description="Arithmetic mean")
    std_dev: float | None = Field(None, description="Sample standard deviation")
    min: float | None = Field(None, description="Minimum value")
    p25: float | None = Field(None, description="25th percentile (Q1)")
    median: float | None = Field(None, description="50th percentile (Median)")
    p75: float | None = Field(None, description="75th percentile (Q3)")
    p90: float | None = Field(None, description="90th percentile")
    max: float | None = Field(None, description="Maximum value")
    iqr: float | None = Field(None, description="Interquartile range")


class SkillDemandSchema(BaseModel):
    """Market demand metric for an individual skill."""

    model_config = ConfigDict(from_attributes=True)

    skill_id: int
    skill_name: str
    category: str
    total_postings: int
    market_penetration_pct: float
    mandatory_count: int
    preferred_count: int
    avg_importance: float


class RoleDistributionSchema(BaseModel):
    """Market share and seniority breakdown for a role archetype."""

    model_config = ConfigDict(from_attributes=True)

    role_name: str
    total_postings: int
    market_share_pct: float
    seniority_breakdown: dict[str, int]
    remote_postings_count: int
    remote_pct: float


class SalaryBenchmarkSchema(BaseModel):
    """Salary distribution benchmark for a specific dimension."""

    model_config = ConfigDict(from_attributes=True)

    dimension_name: str
    dimension_value: str
    stats: DistributionStatsSchema


class LocationDistributionSchema(BaseModel):
    """Geographic market concentration metric."""

    model_config = ConfigDict(from_attributes=True)

    location_name: str
    total_postings: int
    market_share_pct: float
    remote_postings_count: int
    remote_pct: float


class RemoteWorkSummarySchema(BaseModel):
    """Overall and seniority-segmented remote employment metrics."""

    model_config = ConfigDict(from_attributes=True)

    total_active_jobs: int
    total_remote_jobs: int
    overall_remote_pct: float
    remote_by_seniority: dict[str, float]


class MarketOverviewSchema(BaseModel):
    """Executive market intelligence overview summary."""

    model_config = ConfigDict(from_attributes=True)

    total_active_jobs: int
    total_skills_tracked: int
    overall_remote_pct: float
    top_skills: list[SkillDemandSchema]
    top_roles: list[RoleDistributionSchema]
    top_locations: list[LocationDistributionSchema]
