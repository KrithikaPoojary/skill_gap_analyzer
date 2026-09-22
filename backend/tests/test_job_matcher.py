"""Unit tests for JobMatcher multi-factor scoring engine."""

import pytest
from app.services.job_matcher import JobMatcher, JobRequiredSkill, job_matcher


class TestJobMatcherSkillScore:
    """Tests for skill matching and weighting logic."""

    def test_perfect_skill_match(self):
        skills = [
            JobRequiredSkill(name="Python", is_required=True),
            JobRequiredSkill(name="FastAPI", is_required=True),
        ]
        score, matched, missing, missing_req = job_matcher.compute_skill_score(
            ["Python", "FastAPI", "Docker"], skills
        )
        assert score == 100.0
        assert len(matched) == 2
        assert len(missing) == 0
        assert len(missing_req) == 0

    def test_partial_skill_match_with_required_penalty(self):
        skills = [
            JobRequiredSkill(name="Python", is_required=True, importance_weight=1.0),
            JobRequiredSkill(name="Docker", is_required=False, importance_weight=1.0),
        ]
        # Candidate only has the optional skill Docker
        score, matched, missing, missing_req = job_matcher.compute_skill_score(
            ["Docker"], skills
        )
        # Required skill weight = 2.0, optional = 1.0. Total = 3.0. Earned = 1.0 -> 33.3%
        assert 30.0 < score < 35.0
        assert matched == ["Docker"]
        assert missing == ["Python"]
        assert missing_req == ["Python"]

    def test_empty_job_skills_returns_100(self):
        score, matched, missing, missing_req = job_matcher.compute_skill_score(["Python"], [])
        assert score == 100.0


class TestJobMatcherExperienceScore:
    """Tests for experience level alignment."""

    def test_meets_seniority(self):
        score = job_matcher.compute_experience_score(candidate_years=6.0, job_level="senior")
        assert score == 100.0

    def test_below_seniority_graded(self):
        score = job_matcher.compute_experience_score(candidate_years=4.0, job_level="senior")
        assert score == 80.0

    def test_unknown_experience_gives_neutral(self):
        score = job_matcher.compute_experience_score(candidate_years=None, job_level="senior")
        assert score == 50.0


class TestJobMatcherLocationAndSalary:
    """Tests for remote, location, and salary calculations."""

    def test_remote_job_always_100(self):
        score = job_matcher.compute_location_score(
            candidate_location="Seattle",
            candidate_prefers_remote=False,
            job_location="Austin",
            job_is_remote=True,
        )
        assert score == 100.0

    def test_onsite_mismatch_with_remote_preference(self):
        score = job_matcher.compute_location_score(
            candidate_location="Seattle",
            candidate_prefers_remote=True,
            job_location="Austin",
            job_is_remote=False,
        )
        assert score == 30.0

    def test_salary_within_budget(self):
        score = job_matcher.compute_salary_score(
            candidate_desired_salary=120000,
            job_min_salary=100000,
            job_max_salary=140000,
        )
        assert score == 100.0


class TestJobMatcherComposite:
    """Tests for complete match breakdown."""

    def test_strong_candidate_match(self):
        skills = [
            JobRequiredSkill(name="Python", is_required=True),
            JobRequiredSkill(name="PostgreSQL", is_required=False),
        ]
        breakdown = job_matcher.match(
            candidate_skills=["Python", "PostgreSQL"],
            job_skills=skills,
            candidate_years=5.0,
            job_level="mid",
            job_is_remote=True,
            candidate_desired_salary=110000,
            job_max_salary=130000,
        )
        assert breakdown.composite_score >= 85.0
        assert breakdown.match_tier == "Strong"
        assert len(breakdown.missing_skills) == 0
