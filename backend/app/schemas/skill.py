"""Skill and JobSkill association Pydantic validation schemas."""

from pydantic import BaseModel, ConfigDict, Field


class SkillSummary(BaseModel):
    """Compact summary of a skill entity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str


class JobSkillBase(BaseModel):
    """Core attributes linking a skill to a job posting."""

    skill_id: int = Field(..., gt=0, description="Referenced skill ID")
    is_required: bool = Field(True, description="True if mandatory, False if preferred")
    importance_weight: float = Field(
        1.0,
        ge=0.1,
        le=5.0,
        description="Importance multiplier for skill matching (0.1 - 5.0)",
    )


class JobSkillCreate(JobSkillBase):
    """Payload to attach a skill requirement to a job posting."""

    pass


class JobSkillRead(JobSkillBase):
    """Skill requirement specification attached to a job posting response."""

    model_config = ConfigDict(from_attributes=True)

    skill: SkillSummary | None = Field(None, description="Detailed skill metadata")
