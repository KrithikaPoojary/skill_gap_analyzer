"""Job filtering and search query parameter schemas."""

from pydantic import BaseModel, Field

from app.schemas.enums import EmploymentType, ExperienceLevel


class JobFilterParams(BaseModel):
    """Query parameters supported for filtering and searching job postings."""

    query: str | None = Field(None, min_length=1, max_length=100, description="Full-text keyword search")
    title: str | None = Field(None, max_length=100, description="Exact or partial job title")
    company_name: str | None = Field(None, max_length=100, description="Hiring company filter")
    location: str | None = Field(None, max_length=100, description="Location search")
    is_remote: bool | None = Field(None, description="Filter remote positions")
    employment_type: EmploymentType | None = Field(None, description="Employment type filter")
    experience_level: ExperienceLevel | None = Field(None, description="Seniority level filter")
    min_salary: float | None = Field(None, ge=0, description="Minimum compensation threshold")
    max_salary: float | None = Field(None, ge=0, description="Maximum compensation threshold")
    salary_currency: str | None = Field(None, description="Currency filter")
    is_active: bool | None = Field(True, description="Filter active postings only")
    skill_ids: list[int] | None = Field(None, description="Filter jobs requiring specific skill IDs")
