"""Unified market intelligence analytics service.

Orchestrates specialized analytical sub-engines (skills, roles, salaries, geography)
to produce integrated analytical datasets and executive overview summaries.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.job import JobPosting
from app.models.skill import Skill, SkillCategory
from app.schemas.analytics import (
    LocationDistributionSchema,
    MarketOverviewSchema,
    RemoteWorkSummarySchema,
    RoleDistributionSchema,
    SalaryBenchmarkSchema,
    SkillDemandSchema,
)
from app.services.analytics.geo_analyzer import geo_analyzer
from app.services.analytics.role_analyzer import role_analyzer
from app.services.analytics.salary_analyzer import salary_analyzer
from app.services.analytics.skill_analyzer import skill_analyzer


class AnalyticsService:
    """Centralized orchestrator for job market intelligence and analytical queries."""

    def get_market_overview(self, db: Session) -> MarketOverviewSchema:
        """Produce an executive overview of the job market landscape."""
        total_jobs = db.scalar(
            select(func.count(JobPosting.id)).where(JobPosting.is_active.is_(True))
        ) or 0

        total_skills = db.scalar(select(func.count(Skill.id))) or 0

        remote_summary = geo_analyzer.get_remote_summary(db)
        top_skills = skill_analyzer.get_top_skills(db, limit=10)
        top_roles = role_analyzer.get_role_distributions(db)
        top_locations = geo_analyzer.get_top_locations(db, limit=10)

        return MarketOverviewSchema(
            total_active_jobs=total_jobs,
            total_skills_tracked=total_skills,
            overall_remote_pct=remote_summary.overall_remote_pct,
            top_skills=[SkillDemandSchema(**s.to_dict()) for s in top_skills],
            top_roles=[RoleDistributionSchema(**r.to_dict()) for r in top_roles],
            top_locations=[LocationDistributionSchema(**loc.to_dict()) for loc in top_locations],
        )

    def get_skills_analysis(
        self,
        db: Session,
        *,
        limit: int = 20,
        category: SkillCategory | None = None,
    ) -> dict[str, Any]:
        """Fetch ranked skill demand and category distribution breakdown."""
        top_skills = skill_analyzer.get_top_skills(db, limit=limit, category=category)
        category_dist = skill_analyzer.get_category_distribution(db)
        return {
            "top_skills": [s.to_dict() for s in top_skills],
            "category_distribution": category_dist,
        }

    def get_trending_skills(self, db: Session, limit: int = 10, min_importance: float = 0.0) -> list[dict[str, Any]]:
        """Fetch trending skills filtered by importance and ordered by demand."""
        return skill_analyzer.get_trending_skills(db, limit=limit, min_importance=min_importance)

    def get_roles_analysis(self, db: Session) -> list[dict[str, Any]]:
        """Fetch role market share and seniority concentration."""
        roles = role_analyzer.get_role_distributions(db)
        return [r.to_dict() for r in roles]

    def get_salary_analysis(self, db: Session) -> dict[str, Any]:
        """Fetch multidimensional salary benchmarks."""
        by_experience = salary_analyzer.get_salary_by_experience(db)
        by_role = salary_analyzer.get_salary_by_role(db)
        remote_comp = salary_analyzer.get_remote_salary_comparison(db)

        return {
            "by_experience": [r.to_dict() for r in by_experience],
            "by_role": [r.to_dict() for r in by_role],
            "remote_vs_onsite": {k: v.to_dict() for k, v in remote_comp.items()},
        }

    def get_geo_analysis(self, db: Session, limit: int = 15) -> dict[str, Any]:
        """Fetch geographic hiring concentrations and remote-work metrics."""
        locations = geo_analyzer.get_top_locations(db, limit=limit)
        remote_summary = geo_analyzer.get_remote_summary(db)

        return {
            "top_locations": [loc.to_dict() for loc in locations],
            "remote_summary": remote_summary.to_dict(),
        }

    def get_market_breakdown(self, db: Session) -> dict[str, Any]:
        """Fetch market distribution broken down by employment type and experience level."""
        total_active = db.scalar(
            select(func.count(JobPosting.id)).where(JobPosting.is_active.is_(True))
        ) or 0

        # Employment type breakdown
        emp_stmt = (
            select(JobPosting.employment_type, func.count(JobPosting.id))
            .where(JobPosting.is_active.is_(True))
            .group_by(JobPosting.employment_type)
        )
        emp_rows = db.execute(emp_stmt).all()
        employment_types = [
            {
                "employment_type": row[0],
                "count": row[1],
                "percentage": round((row[1] / total_active * 100), 2) if total_active > 0 else 0.0,
            }
            for row in sorted(emp_rows, key=lambda x: x[1], reverse=True)
        ]

        # Experience level breakdown
        exp_stmt = (
            select(JobPosting.experience_level, func.count(JobPosting.id))
            .where(JobPosting.is_active.is_(True))
            .group_by(JobPosting.experience_level)
        )
        exp_rows = db.execute(exp_stmt).all()
        experience_levels = [
            {
                "experience_level": row[0],
                "count": row[1],
                "percentage": round((row[1] / total_active * 100), 2) if total_active > 0 else 0.0,
            }
            for row in sorted(exp_rows, key=lambda x: x[1], reverse=True)
        ]

        return {
            "total_active_jobs": total_active,
            "by_employment_type": employment_types,
            "by_experience_level": experience_levels,
        }

    def get_platform_summary(self, db: Session) -> dict[str, Any]:
        """Produce high-level KPI metrics summary for platform intelligence."""
        from app.models.role import TargetRole
        from app.models.user import User

        active_jobs = db.scalar(select(func.count(JobPosting.id)).where(JobPosting.is_active.is_(True))) or 0
        total_skills = db.scalar(select(func.count(Skill.id))) or 0
        total_roles = db.scalar(select(func.count(TargetRole.id)).where(TargetRole.is_active.is_(True))) or 0
        total_users = db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
        remote_summary = geo_analyzer.get_remote_summary(db)

        return {
            "active_jobs": active_jobs,
            "total_skills": total_skills,
            "total_target_roles": total_roles,
            "total_active_users": total_users,
            "remote_job_ratio_pct": remote_summary.overall_remote_pct,
        }


analytics_service = AnalyticsService()
