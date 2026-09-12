"""Job posting Pydantic request and response validation schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    salary_currency: str = Field("USD", description="3-letter ISO Currency code")
    description: str = Field(..., min_length=10, description="Full job description")
    requirements_raw: str | None = Field(None, description="Raw bulleted requirements")
    source_url: str | None = Field(None, max_length=500, description="Origin listing URL")
    source_platform: SourcePlatform = Field(
        default=SourcePlatform.MANUAL,
        description="Source channel",
    )
    is_active: bool = Field(True, description="Whether posting is active")

    @field_validator("salary_currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        """Strip whitespace and enforce uppercase 3-letter ISO code."""
        cleaned = v.strip().upper()
        if len(cleaned) != 3:
            raise ValueError("Currency code must be a 3-letter ISO code (e.g. USD, EUR, INR)")
        return cleaned

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobBase":
        """Ensure min_salary is not greater than max_salary when both are specified."""
        if self.min_salary is not None and self.max_salary is not None:
            if self.min_salary > self.max_salary:
                raise ValueError("min_salary cannot be greater than max_salary")
        return self


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
    salary_currency: str | None = None
    description: str | None = Field(None, min_length=10)
    requirements_raw: str | None = None
    source_url: str | None = Field(None, max_length=500)
    source_platform: SourcePlatform | None = None
    is_active: bool | None = None

    @field_validator("salary_currency")
    @classmethod
    def normalize_currency(cls, v: str | None) -> str | None:
        """Strip whitespace and enforce uppercase 3-letter ISO code."""
        if v is not None:
            cleaned = v.strip().upper()
            if len(cleaned) != 3:
                raise ValueError("Currency code must be a 3-letter ISO code (e.g. USD, EUR, INR)")
            return cleaned
        return v

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobUpdate":
        """Ensure min_salary is not greater than max_salary when both are specified."""
        if self.min_salary is not None and self.max_salary is not None:
            if self.min_salary > self.max_salary:
                raise ValueError("min_salary cannot be greater than max_salary")
        return self


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
