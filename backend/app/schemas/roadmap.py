"""Pydantic schemas for Personalized Learning Roadmaps."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class LearningResourceDTO(BaseModel):
    """Curated learning resource for a skill."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    url: str
    resource_type: str = "official_docs"
    is_free: bool = True


class MilestoneSkillDTO(BaseModel):
    """Skill item within a roadmap milestone phase."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    category: str = "other"
    difficulty: str = "intermediate"
    estimated_hours: int = 10
    recommended_practice: str = ""
    is_completed: bool = False
    resources: list[LearningResourceDTO] = Field(default_factory=list)


class RoadmapMilestoneDTO(BaseModel):
    """Progressive milestone phase within a learning roadmap."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    phase_number: int
    phase_title: str
    description: str | None = None
    total_phase_hours: int = 0
    estimated_weeks: int = 1
    capstone_project_title: str | None = None
    capstone_project_description: str | None = None
    is_completed: bool = False
    skills: list[MilestoneSkillDTO] = Field(default_factory=list)


class RoadmapGenerateRequest(BaseModel):
    """Payload to generate a roadmap from an explicit skill deficit list."""

    missing_skills: list[str] = Field(..., min_length=1, description="Deficit skills to sequence")
    role_title: str = Field("Target Role", max_length=150, description="Target career role title")
    weekly_commitment_hours: int = Field(
        10,
        ge=1,
        le=80,
        description="Weekly study availability in hours",
    )


class RoadmapGenerateFromTextRequest(BaseModel):
    """Payload to extract skills from text, compare against a target role, and generate roadmap."""

    text: str = Field(..., min_length=3, description="Resume or profile unstructured text")
    role_name: str | None = Field(None, max_length=100, description="Target role title")
    role_slug: str | None = Field(None, max_length=100, description="Target role slug")
    weekly_commitment_hours: int = Field(10, ge=1, le=80)
    min_confidence: float = Field(0.60, ge=0.0, le=1.0)


class RoadmapResponse(BaseModel):
    """Full personalized roadmap response representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    title: str
    target_role_name: str
    total_skills: int
    total_estimated_hours: int
    weekly_commitment_hours: int
    estimated_weeks: int
    status: str = "active"
    milestones: list[RoadmapMilestoneDTO] = Field(default_factory=list)


class MilestoneProgressUpdateRequest(BaseModel):
    """Payload to toggle milestone completion."""

    is_completed: bool = Field(..., description="Mark milestone completed or pending")
