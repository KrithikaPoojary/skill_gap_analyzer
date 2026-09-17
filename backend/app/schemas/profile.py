"""Pydantic DTO schemas for user profiles and user skills."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserSkillCreateRequest(BaseModel):
    """Payload to add or update a skill on a user's profile."""

    skill_id: int | None = Field(None, gt=0, description="Existing skill ID from taxonomy")
    skill_name: str | None = Field(None, max_length=100, description="Skill name if ID not known")
    proficiency_level: str = Field(
        "intermediate",
        pattern=r"^(beginner|intermediate|advanced|expert)$",
        description="Proficiency level: beginner, intermediate, advanced, expert",
    )
    years_of_experience: float = Field(
        1.0,
        ge=0.0,
        le=60.0,
        description="Years of hands-on experience",
    )
    is_verified: bool = Field(False, description="Whether verified by assessment or credential")


class UserSkillResponse(BaseModel):
    """Details of a user's associated skill."""

    model_config = ConfigDict(from_attributes=True)

    skill_id: int
    name: str | None = None
    normalized_name: str | None = None
    category: str | None = None
    proficiency_level: str
    years_of_experience: float
    is_verified: bool


class ProfileData(BaseModel):
    """Candidate profile detail attributes."""

    model_config = ConfigDict(from_attributes=True)

    headline: str | None = None
    bio: str | None = None
    current_title: str | None = None
    years_of_experience: float = 0.0
    location: str | None = None
    resume_url: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None


class ProfileUpsertRequest(BaseModel):
    """Payload to create or modify candidate profile attributes."""

    headline: str | None = Field(None, max_length=255)
    bio: str | None = None
    current_title: str | None = Field(None, max_length=100)
    years_of_experience: float | None = Field(None, ge=0.0, le=60.0)
    location: str | None = Field(None, max_length=150)
    resume_url: str | None = Field(None, max_length=500)
    github_url: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=255)


class TargetRoleSummary(BaseModel):
    """Summary of a target career role attached to a user."""

    model_config = ConfigDict(from_attributes=True)

    role_id: int
    title: str | None = None
    slug: str | None = None
    readiness_score: float = 0.0
    target_date: str | None = None


class FullProfileResponse(BaseModel):
    """Complete aggregated user profile response."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: str
    full_name: str | None = None
    profile: ProfileData
    skills: list[UserSkillResponse] = Field(default_factory=list)
    target_roles: list[TargetRoleSummary] = Field(default_factory=list)
