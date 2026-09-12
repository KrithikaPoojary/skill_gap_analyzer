"""Unit tests for JobSkill and Skill association schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.job import JobCreate, JobRead
from app.schemas.skill import JobSkillCreate, JobSkillRead, SkillSummary


class TestJobSkillSchemas:
    """Test suite for JobSkill association schemas and nesting."""

    def test_valid_job_skill_create(self) -> None:
        js = JobSkillCreate(skill_id=5, is_required=True, importance_weight=4.5)
        assert js.skill_id == 5
        assert js.is_required is True
        assert js.importance_weight == 4.5

    def test_job_skill_default_weight(self) -> None:
        js = JobSkillCreate(skill_id=1)
        assert js.importance_weight == 1.0
        assert js.is_required is True

    def test_job_skill_invalid_weight_range(self) -> None:
        # Weight too low
        with pytest.raises(ValidationError):
            JobSkillCreate(skill_id=1, importance_weight=0.05)

        # Weight too high
        with pytest.raises(ValidationError):
            JobSkillCreate(skill_id=1, importance_weight=6.0)

    def test_job_create_with_nested_skills(self) -> None:
        job = JobCreate(
            title="Senior Fullstack Engineer",
            company_name="Acme Tech",
            description="Developing scalable web applications.",
            skills=[
                JobSkillCreate(skill_id=1, is_required=True, importance_weight=5.0),
                JobSkillCreate(skill_id=2, is_required=False, importance_weight=2.5),
            ],
        )
        assert len(job.skills) == 2
        assert job.skills[0].skill_id == 1
        assert job.skills[0].is_required is True
        assert job.skills[1].skill_id == 2
        assert job.skills[1].is_required is False

    def test_job_skill_read_with_summary(self) -> None:
        summary = SkillSummary(id=1, name="Python", category="language")
        js_read = JobSkillRead(skill_id=1, is_required=True, importance_weight=5.0, skill=summary)
        assert js_read.skill is not None
        assert js_read.skill.name == "Python"
        assert js_read.skill.category == "language"
