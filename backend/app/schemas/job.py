"""Job posting Pydantic request and response validation schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import (
    Currency,
    EmploymentType,
    ExperienceLevel,
    SourcePlatform,
)


class JobBase(BaseModel):
    """Shared attributes present across all job representations."""

    title: str = Field(..., min_length=2, max_length=200, description="Job title")
    company_name: str = Field(..., min_length=1, max_length=150, description="Hiring company")
    location: str | None = Field(None, max_length=150, description="Office location or region")
    is_remote: bool = Field(False, description="Whether position is fully remote")
    employment_type: EmploymentType = Field(
        default=EmploymentType.FULL_TIME,
        description="Employment commitment",
    )
    experience_level: ExperienceLevel = Field(
        default=ExperienceLevel.MID,
        description="Required seniority stage",
    )
    min_salary: float | None = Field(None, ge=0, description="Minimum annualized salary")
    max_salary: float | None = Field(None, ge=0, description="Maximum annualized salary")
    salary_currency: str = Field("USD", min_length=3, max_length=10, description="ISO Currency code")
    description: str = Field(..., min_length=10, description="Full job description")
    requirements_raw: str | None = Field(None, description="Raw bulleted requirements")
    source_url: str | None = Field(None, max_length=500, description="Origin listing URL")
    source_platform: SourcePlatform = Field(
        default=SourcePlatform.MANUAL,
        description="Source channel",
    )
    is_active: bool = Field(True, description="Whether posting is active")


class JobCreate(JobBase):
    """Payload for creating a new job posting."""

    pass


class JobUpdate(BaseModel):
    """Payload for updating an existing job posting (all fields optional)."""

    title: str | None = Field(None, min_length=2, max_length=200)
    company_name: str | None = Field(None, min_length=1, max_length=150)
    location: str | None = Field(None, max_length=150)
    is_remote: bool | None = None
    employment_type: EmploymentType | None = None
    experience_level: ExperienceLevel | None = None
    min_salary: float | None = Field(None, ge=0)
    max_salary: float | None = Field(None, ge=0)
    salary_currency: str | None = Field(None, min_length=3, max_length=10)
    description: str | None = Field(None, min_length=10)
    requirements_raw: str | None = None
    source_url: str | None = Field(None, max_length=500)
    source_platform: SourcePlatform | None = None
    is_active: bool | None = None


class JobInDB(JobBase):
    """Internal database representation of a job posting."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    posted_date: datetime
    created_at: datetime
    updated_at: datetime


class JobRead(JobInDB):
    """Public client response schema for a job posting."""

    pass
