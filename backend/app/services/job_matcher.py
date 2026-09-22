"""Quantitative job matching algorithm and multi-factor scoring engine.

Implements Module 3 of Project Specification:
- Base Skill Overlap Calculation: |User Skills ∩ Required Skills| / |Required Skills| * 100
- Weighted Matching: Distinguish mandatory prerequisites from preferred skills.
- Multi-factor Scoring: Combines skills, experience fit, location/remote, and salary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class JobRequiredSkill:
    """Represents a skill requirement associated with a job posting."""

    name: str
    is_required: bool = True
    importance_weight: float = 1.0


@dataclass
class JobMatchBreakdown:
    """Detailed quantitative breakdown of a job match calculation."""

    skill_score: float  # [0.0, 100.0]
    experience_score: float  # [0.0, 100.0]
    location_score: float  # [0.0, 100.0]
    salary_score: float  # [0.0, 100.0]
    composite_score: float  # [0.0, 100.0]
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    missing_required_skills: list[str] = field(default_factory=list)
    match_tier: str = "Low"  # "Strong", "Moderate", "Low"

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_score": round(self.skill_score, 2),
            "experience_score": round(self.experience_score, 2),
            "location_score": round(self.location_score, 2),
            "salary_score": round(self.salary_score, 2),
            "composite_score": round(self.composite_score, 2),
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "missing_required_skills": self.missing_required_skills,
            "match_tier": self.match_tier,
        }


class JobMatcher:
    """Evaluates candidate profiles against individual job postings with multi-factor scoring."""

    SKILL_WEIGHT = 0.60
    EXPERIENCE_WEIGHT = 0.20
    LOCATION_WEIGHT = 0.10
    SALARY_WEIGHT = 0.10

    EXPERIENCE_MAP: dict[str, float] = {
        "entry": 0.0,
        "junior": 1.0,
        "mid": 3.0,
        "senior": 5.0,
        "lead": 7.0,
        "principal": 10.0,
        "executive": 12.0,
    }

    def compute_skill_score(
        self,
        candidate_skills: list[str],
        job_skills: list[JobRequiredSkill],
    ) -> tuple[float, list[str], list[str], list[str]]:
        if not job_skills:
            return 100.0, candidate_skills[:], [], []

        norm_candidate = {s.strip().lower() for s in candidate_skills if s and s.strip()}
        total_possible_points = 0.0
        earned_points = 0.0

        matched: list[str] = []
        missing: list[str] = []
        missing_required: list[str] = []

        for req in job_skills:
            norm_name = req.name.strip().lower()
            weight = req.importance_weight * (2.0 if req.is_required else 1.0)
            total_possible_points += weight

            if norm_name in norm_candidate:
                earned_points += weight
                matched.append(req.name)
            else:
                missing.append(req.name)
                if req.is_required:
                    missing_required.append(req.name)

        if total_possible_points <= 0.0:
            return 100.0, matched, missing, missing_required

        raw_score = (earned_points / total_possible_points) * 100.0
        return min(100.0, max(0.0, raw_score)), matched, missing, missing_required

    def compute_experience_score(
        self,
        candidate_years: float | None,
        job_level: str | None,
        job_min_years: float | None = None,
    ) -> float:
        expected_years = 0.0
        if job_min_years is not None:
            expected_years = float(job_min_years)
        elif job_level:
            expected_years = self.EXPERIENCE_MAP.get(job_level.lower(), 2.0)

        if candidate_years is None:
            return 50.0

        if candidate_years >= expected_years:
            return 100.0

        gap = expected_years - candidate_years
        if gap <= 1.0:
            return 80.0
        if gap <= 2.0:
            return 60.0
        if gap <= 3.0:
            return 40.0
        return 20.0

    def compute_location_score(
        self,
        candidate_location: str | None,
        candidate_prefers_remote: bool | None,
        job_location: str | None,
        job_is_remote: bool | None,
    ) -> float:
        if job_is_remote:
            return 100.0

        if candidate_prefers_remote and not job_is_remote:
            return 30.0

        if not candidate_location or not job_location:
            return 70.0

        c_loc = candidate_location.strip().lower()
        j_loc = job_location.strip().lower()

        if c_loc == j_loc or c_loc in j_loc or j_loc in c_loc:
            return 100.0

        return 40.0

    def compute_salary_score(
        self,
        candidate_desired_salary: float | None,
        job_min_salary: float | None,
        job_max_salary: float | None,
    ) -> float:
        if candidate_desired_salary is None:
            return 80.0

        if job_max_salary is not None and job_max_salary > 0:
            if candidate_desired_salary <= job_max_salary:
                return 100.0
            excess = candidate_desired_salary - job_max_salary
            pct_over = excess / job_max_salary
            if pct_over <= 0.10:
                return 75.0
            if pct_over <= 0.25:
                return 50.0
            return 25.0

        if job_min_salary is not None and job_min_salary > 0:
            if candidate_desired_salary <= job_min_salary * 1.2:
                return 90.0
            return 50.0

        return 75.0

    def match(
        self,
        *,
        candidate_skills: list[str],
        job_skills: list[JobRequiredSkill],
        candidate_years: float | None = None,
        job_level: str | None = None,
        job_min_years: float | None = None,
        candidate_location: str | None = None,
        candidate_prefers_remote: bool | None = None,
        job_location: str | None = None,
        job_is_remote: bool | None = None,
        candidate_desired_salary: float | None = None,
        job_min_salary: float | None = None,
        job_max_salary: float | None = None,
    ) -> JobMatchBreakdown:
        skill_score, matched, missing, missing_req = self.compute_skill_score(
            candidate_skills, job_skills
        )
        exp_score = self.compute_experience_score(candidate_years, job_level, job_min_years)
        loc_score = self.compute_location_score(
            candidate_location, candidate_prefers_remote, job_location, job_is_remote
        )
        sal_score = self.compute_salary_score(
            candidate_desired_salary, job_min_salary, job_max_salary
        )

        composite = (
            skill_score * self.SKILL_WEIGHT
            + exp_score * self.EXPERIENCE_WEIGHT
            + loc_score * self.LOCATION_WEIGHT
            + sal_score * self.SALARY_WEIGHT
        )

        if composite >= 75.0 and not missing_req:
            tier = "Strong"
        elif composite >= 50.0:
            tier = "Moderate"
        else:
            tier = "Low"

        return JobMatchBreakdown(
            skill_score=skill_score,
            experience_score=exp_score,
            location_score=loc_score,
            salary_score=sal_score,
            composite_score=composite,
            matched_skills=matched,
            missing_skills=missing,
            missing_required_skills=missing_req,
            match_tier=tier,
        )


job_matcher = JobMatcher()
