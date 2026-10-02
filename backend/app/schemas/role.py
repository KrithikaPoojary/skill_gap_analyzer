"""Target role and user target role Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TargetRoleBase(BaseModel):
    title: str = Field(..., max_length=100, description="Role title")
    slug: str = Field(..., max_length=100, description="URL-friendly identifier")
    description: str | None = Field(None, description="Detailed role description")
    category: str = Field("Software Engineering", max_length=50, description="Industry sector")
    min_experience_years: float = Field(1.0, ge=0.0, description="Minimum recommended years of experience")


class TargetRoleCreate(TargetRoleBase):
    pass


class TargetRoleRead(TargetRoleBase):
    id: int
    is_active: bool = True
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RoleSkillItem(BaseModel):
    skill_id: int
    skill_name: str | None = None
    weight: float = 1.0
    is_core: bool = True
    benchmark_level: str = "intermediate"

    model_config = ConfigDict(from_attributes=True)


class TargetRoleDetailRead(TargetRoleRead):
    skills: list[RoleSkillItem] = Field(default_factory=list)


class UserTargetRoleCreate(BaseModel):
    role_id: int = Field(..., description="Target role ID to associate")
    target_date: datetime | None = Field(None, description="Target achievement target date")


class UserTargetRoleRead(BaseModel):
    user_id: int
    role_id: int
    role_title: str | None = None
    role_category: str | None = None
    readiness_score: float = 0.0
    target_date: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
