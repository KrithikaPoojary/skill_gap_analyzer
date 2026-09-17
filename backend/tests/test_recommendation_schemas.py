"""Unit tests for recommendation and gap analysis schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.gap_analysis import (
    GapAnalysisSkillsRequest,
    GapAnalysisTextRequest,
    GapReportSchema,
)
from app.schemas.recommendations import (
    RecommendationsForSkillsRequest,
    RecommendationsForTextRequest,
    RoleRecommendationItem,
)


class TestRecommendationSchemas:
    def test_role_recommendation_item_valid(self):
        item = RoleRecommendationItem(
            role_id=1,
            title="Backend Developer",
            slug="backend-dev",
            category="Software Engineering",
            min_experience_years=2.0,
            match_score=0.85,
            coverage_pct=75.0,
            matched_skills=["Python", "FastAPI"],
            missing_skills=[{"name": "Docker", "weight": 0.8}],
            missing_critical=["Docker"],
        )
        data = item.model_dump()
        assert data["match_score"] == 0.85
        assert len(data["matched_skills"]) == 2

    def test_role_recommendation_invalid_score(self):
        with pytest.raises(ValidationError):
            RoleRecommendationItem(
                role_id=1,
                title="Test",
                slug="test",
                category="Engineering",
                match_score=1.5,  # > 1.0 invalid
                coverage_pct=50.0,
            )

    def test_recommendations_for_skills_request(self):
        req = RecommendationsForSkillsRequest(
            skills=["Python", "SQL"],
            limit=10,
            min_score=0.2,
        )
        assert len(req.skills) == 2
        assert req.limit == 10

    def test_recommendations_for_text_request(self):
        req = RecommendationsForTextRequest(
            text="Experienced in Python and Docker container orchestration.",
            limit=3,
        )
        assert req.limit == 3
        assert req.min_confidence == 0.60

    def test_gap_analysis_skills_request(self):
        req = GapAnalysisSkillsRequest(
            skills=["Python", "React"],
            role_slug="fullstack-developer",
        )
        assert req.role_slug == "fullstack-developer"

    def test_gap_report_schema(self):
        schema = GapReportSchema(
            role_name="DevOps Engineer",
            gap_score=0.6,
            weighted_gap_score=0.72,
            coverage_pct=60.0,
            matched_skills=["Docker", "Linux"],
            missing_skills=[{"name": "Terraform", "weight": 0.9}],
        )
        d = schema.model_dump()
        assert d["role_name"] == "DevOps Engineer"
        assert d["coverage_pct"] == 60.0
