"""Job matching database service layer.

Coordinates database queries across active job postings, formats requirements,
executes multi-factor match calculations, and returns ranked match results.
"""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.associations import JobSkill, UserSkill
from app.models.job import JobPosting
from app.models.user import Profile, User
from app.schemas.job_match import (
    JobMatchCriteria,
    JobMatchResult,
    JobMatchScoreDetail,
    PaginatedJobMatchResponse,
)
from app.services.job_matcher import JobMatcher, JobRequiredSkill, job_matcher


class JobMatchService:
    """Coordinates database fetching and multi-factor ranking of job postings."""

    def __init__(self, matcher: JobMatcher | None = None) -> None:
        self.matcher = matcher or job_matcher

    def _get_active_jobs_with_skills(self, db: Session) -> list[JobPosting]:
        """Fetch all active job postings with their associated skill requirements."""
        stmt = (
            select(JobPosting)
            .where(JobPosting.is_active.is_(True))
            .options(joinedload(JobPosting.job_skills).joinedload(JobSkill.skill))
        )
        return list(db.scalars(stmt).unique().all())

    def match_jobs(
        self,
        db: Session,
        criteria: JobMatchCriteria,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> PaginatedJobMatchResponse:
        """Score and rank all active job postings against input candidate criteria."""
        jobs = self._get_active_jobs_with_skills(db)
        matched_results: list[JobMatchResult] = []

        for job in jobs:
            job_req_skills: list[JobRequiredSkill] = []
            for js in job.job_skills:
                if js.skill and js.skill.name:
                    job_req_skills.append(
                        JobRequiredSkill(
                            name=js.skill.name,
                            is_required=js.is_required,
                            importance_weight=js.importance_weight,
                        )
                    )

            breakdown = self.matcher.match(
                candidate_skills=criteria.skills,
                job_skills=job_req_skills,
                candidate_years=criteria.years_of_experience,
                job_level=job.experience_level,
                candidate_location=criteria.location,
                candidate_prefers_remote=criteria.prefers_remote,
                job_location=job.location,
                job_is_remote=job.is_remote,
                candidate_desired_salary=criteria.desired_salary,
                job_min_salary=job.min_salary,
                job_max_salary=job.max_salary,
            )

            if breakdown.composite_score >= criteria.min_match_score:
                score_detail = JobMatchScoreDetail(
                    skill_score=breakdown.skill_score,
                    experience_score=breakdown.experience_score,
                    location_score=breakdown.location_score,
                    salary_score=breakdown.salary_score,
                    composite_score=breakdown.composite_score,
                    match_tier=breakdown.match_tier,
                    matched_skills=breakdown.matched_skills,
                    missing_skills=breakdown.missing_skills,
                    missing_required_skills=breakdown.missing_required_skills,
                )

                matched_results.append(
                    JobMatchResult(
                        job_id=job.id,
                        title=job.title,
                        company_name=job.company_name,
                        location=job.location,
                        is_remote=job.is_remote,
                        employment_type=job.employment_type,
                        experience_level=job.experience_level,
                        min_salary=job.min_salary,
                        max_salary=job.max_salary,
                        currency=job.salary_currency,
                        posted_date=job.posted_date,
                        match_detail=score_detail,
                    )
                )

        # Sort highest composite score first
        matched_results.sort(key=lambda r: r.match_detail.composite_score, reverse=True)

        total = len(matched_results)
        paginated_items = matched_results[offset : offset + limit]

        return PaginatedJobMatchResponse(
            items=paginated_items,
            total=total,
            offset=offset,
            limit=limit,
        )

    def match_for_user(
        self,
        db: Session,
        *,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
        min_match_score: float = 0.0,
    ) -> PaginatedJobMatchResponse:
        """Extract user's claimed skills and profile data, then compute ranked matches."""
        user = db.get(User, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        # Get user skills
        user_skills_stmt = (
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .options(joinedload(UserSkill.skill))
        )
        user_skills = list(db.scalars(user_skills_stmt).unique().all())
        skill_names = [us.skill.name for us in user_skills if us.skill and us.skill.name]

        profile = db.scalar(select(Profile).where(Profile.user_id == user_id))

        criteria = JobMatchCriteria(
            skills=skill_names if skill_names else ["Software Engineering"],
            years_of_experience=profile.years_of_experience if profile else None,
            location=profile.location if profile else None,
            min_match_score=min_match_score,
        )

        return self.match_jobs(db, criteria, offset=offset, limit=limit)

    def match_single_job(
        self,
        db: Session,
        *,
        job_id: int,
        candidate_skills: list[str],
        candidate_years: float | None = None,
        candidate_location: str | None = None,
        candidate_desired_salary: float | None = None,
    ) -> JobMatchScoreDetail | None:
        """Compute match breakdown between candidate criteria and a single specific job."""
        stmt = (
            select(JobPosting)
            .where(JobPosting.id == job_id)
            .options(joinedload(JobPosting.job_skills).joinedload(JobSkill.skill))
        )
        job = db.scalar(stmt)
        if not job:
            return None

        job_req_skills: list[JobRequiredSkill] = []
        for js in job.job_skills:
            if js.skill and js.skill.name:
                job_req_skills.append(
                    JobRequiredSkill(
                        name=js.skill.name,
                        is_required=js.is_required,
                        importance_weight=js.importance_weight,
                    )
                )

        breakdown = self.matcher.match(
            candidate_skills=candidate_skills,
            job_skills=job_req_skills,
            candidate_years=candidate_years,
            job_level=job.experience_level,
            candidate_location=candidate_location,
            job_location=job.location,
            job_is_remote=job.is_remote,
            candidate_desired_salary=candidate_desired_salary,
            job_min_salary=job.min_salary,
            job_max_salary=job.max_salary,
        )

        return JobMatchScoreDetail(
            skill_score=breakdown.skill_score,
            experience_score=breakdown.experience_score,
            location_score=breakdown.location_score,
            salary_score=breakdown.salary_score,
            composite_score=breakdown.composite_score,
            match_tier=breakdown.match_tier,
            matched_skills=breakdown.matched_skills,
            missing_skills=breakdown.missing_skills,
            missing_required_skills=breakdown.missing_required_skills,
        )


job_match_service = JobMatchService()
