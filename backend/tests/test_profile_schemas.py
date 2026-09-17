"""Unit tests for profile schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.profile import (
    FullProfileResponse,
    ProfileData,
    ProfileUpsertRequest,
    TargetRoleSummary,
    UserSkillCreateRequest,
    UserSkillResponse,
)


class TestProfileSchemas:
    def test_user_skill_create_valid(self):
        req = UserSkillCreateRequest(
            skill_id=10,
            proficiency_level="expert",
            years_of_experience=5.0,
            is_verified=True,
        )
        assert req.skill_id == 10
        assert req.proficiency_level == "expert"
        assert req.years_of_experience == 5.0
        assert req.is_verified is True

    def test_user_skill_create_invalid_proficiency(self):
        with pytest.raises(ValidationError):
            UserSkillCreateRequest(proficiency_level="master")

    def test_user_skill_create_negative_exp(self):
        with pytest.raises(ValidationError):
            UserSkillCreateRequest(years_of_experience=-1.0)

    def test_user_skill_response_serialization(self):
        resp = UserSkillResponse(
            skill_id=1,
            name="Python",
            normalized_name="python",
            category="language",
            proficiency_level="intermediate",
            years_of_experience=3.0,
            is_verified=False,
        )
        dumped = resp.model_dump()
        assert dumped["name"] == "Python"
        assert dumped["skill_id"] == 1

    def test_profile_upsert_valid(self):
        req = ProfileUpsertRequest(
            headline="Full Stack Engineer",
            years_of_experience=4.0,
            github_url="https://github.com/test",
        )
        assert req.headline == "Full Stack Engineer"
        assert req.years_of_experience == 4.0

    def test_full_profile_response(self):
        resp = FullProfileResponse(
            user_id=42,
            email="engineer@test.com",
            full_name="Jane Doe",
            profile=ProfileData(
                headline="DevOps Specialist",
                years_of_experience=6.0,
                location="San Francisco, CA",
            ),
            skills=[
                UserSkillResponse(
                    skill_id=2,
                    name="Docker",
                    proficiency_level="advanced",
                    years_of_experience=4.0,
                    is_verified=True,
                )
            ],
            target_roles=[
                TargetRoleSummary(
                    role_id=5,
                    title="Site Reliability Engineer",
                    slug="site-reliability-engineer",
                    readiness_score=0.92,
                )
            ],
        )
        data = resp.model_dump()
        assert data["user_id"] == 42
        assert data["profile"]["headline"] == "DevOps Specialist"
        assert len(data["skills"]) == 1
        assert len(data["target_roles"]) == 1
