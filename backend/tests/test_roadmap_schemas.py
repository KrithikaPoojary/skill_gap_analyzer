"""Unit tests for roadmap schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.roadmap import (
    LearningResourceDTO,
    MilestoneProgressUpdateRequest,
    MilestoneSkillDTO,
    RoadmapGenerateFromTextRequest,
    RoadmapGenerateRequest,
    RoadmapMilestoneDTO,
    RoadmapResponse,
)


class TestRoadmapSchemas:
    def test_learning_resource_dto(self):
        dto = LearningResourceDTO(
            title="FastAPI Docs",
            url="https://fastapi.tiangolo.com/",
            resource_type="official_docs",
            is_free=True,
        )
        d = dto.model_dump()
        assert d["title"] == "FastAPI Docs"
        assert d["is_free"] is True

    def test_milestone_skill_dto(self):
        dto = MilestoneSkillDTO(
            name="Docker",
            category="cloud_devops",
            difficulty="intermediate",
            estimated_hours=18,
            resources=[
                LearningResourceDTO(title="Docker Docs", url="https://docs.docker.com/")
            ],
        )
        assert dto.name == "Docker"
        assert len(dto.resources) == 1

    def test_roadmap_generate_request_validation(self):
        req = RoadmapGenerateRequest(
            missing_skills=["Python", "FastAPI"],
            role_title="Backend Developer",
            weekly_commitment_hours=15,
        )
        assert len(req.missing_skills) == 2
        assert req.weekly_commitment_hours == 15

    def test_roadmap_generate_request_empty_skills_invalid(self):
        with pytest.raises(ValidationError):
            RoadmapGenerateRequest(missing_skills=[])

    def test_roadmap_generate_request_invalid_hours(self):
        with pytest.raises(ValidationError):
            RoadmapGenerateRequest(missing_skills=["Python"], weekly_commitment_hours=0)

    def test_roadmap_generate_from_text_request(self):
        req = RoadmapGenerateFromTextRequest(
            text="I know basic Python and SQL.",
            role_slug="backend-developer",
            weekly_commitment_hours=10,
        )
        assert req.role_slug == "backend-developer"
        assert req.min_confidence == 0.60

    def test_roadmap_response_serialization(self):
        resp = RoadmapResponse(
            id=1,
            title="Data Science Roadmap",
            target_role_name="Data Scientist",
            total_skills=4,
            total_estimated_hours=80,
            weekly_commitment_hours=10,
            estimated_weeks=8,
            status="active",
            milestones=[
                RoadmapMilestoneDTO(
                    id=10,
                    phase_number=1,
                    phase_title="Foundations",
                    total_phase_hours=40,
                    estimated_weeks=4,
                    skills=[MilestoneSkillDTO(name="Python", estimated_hours=40)],
                )
            ],
        )
        data = resp.model_dump()
        assert data["id"] == 1
        assert data["target_role_name"] == "Data Scientist"
        assert len(data["milestones"]) == 1
        assert data["milestones"][0]["skills"][0]["name"] == "Python"

    def test_milestone_progress_update_request(self):
        req = MilestoneProgressUpdateRequest(is_completed=True)
        assert req.is_completed is True
