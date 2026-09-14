"""Salary distribution and compensation benchmark analytics service.

Computes salary statistics (min, p25, median, p75, max) segmented by
experience level, role track, remote work status, and key skills.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill
from app.schemas.enums import ExperienceLevel
from app.services.analytics.stats import DistributionSummary, summarize_distribution


@dataclass(frozen=True)
class SalaryBenchmarkRecord:
    """Salary benchmark metrics for a specific dimension."""

    dimension_name: str
    dimension_value: str
    stats: DistributionSummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension_name": self.dimension_name,
            "dimension_value": self.dimension_value,
            "stats": self.stats.to_dict(),
        }


class SalaryAnalyzer:
    """Computes multidimensional salary benchmarks."""

    def _extract_midpoints(self, postings: list[JobPosting]) -> list[float]:
        """Extract average annual salary midpoints for postings with valid salary figures."""
        salaries: list[float] = []
        for p in postings:
            if p.min_salary and p.max_salary:
                salaries.append((p.min_salary + p.max_salary) / 2.0)
            elif p.min_salary:
                salaries.append(p.min_salary)
            elif p.max_salary:
                salaries.append(p.max_salary)
        return salaries

    def get_salary_by_experience(self, db: Session) -> list[SalaryBenchmarkRecord]:
        """Compute salary benchmarks grouped by seniority level."""
        records = []
        for level in ExperienceLevel:
            postings = list(
                db.scalars(
                    select(JobPosting).where(
                        JobPosting.is_active.is_(True),
                        JobPosting.experience_level == level.value,
                    )
                ).all()
            )
            salaries = self._extract_midpoints(postings)
            summary = summarize_distribution(salaries)
            records.append(
                SalaryBenchmarkRecord(
                    dimension_name="experience_level",
                    dimension_value=level.value,
                    stats=summary,
                )
            )
        return records

    def get_salary_by_role(self, db: Session, roles: list[str] | None = None) -> list[SalaryBenchmarkRecord]:
        """Compute salary benchmarks for key engineering roles."""
        role_list = roles or [
            "Backend",
            "Frontend",
            "Full Stack",
            "DevOps",
            "Data Engineer",
            "Machine Learning",
            "QA Automation",
        ]
        records = []
        for role in role_list:
            postings = list(
                db.scalars(
                    select(JobPosting).where(
                        JobPosting.is_active.is_(True),
                        JobPosting.title.ilike(f"%{role}%"),
                    )
                ).all()
            )
            salaries = self._extract_midpoints(postings)
            summary = summarize_distribution(salaries)
            records.append(
                SalaryBenchmarkRecord(
                    dimension_name="role",
                    dimension_value=role,
                    stats=summary,
                )
            )
        return records

    def get_remote_salary_comparison(self, db: Session) -> dict[str, DistributionSummary]:
        """Compare salary distributions between remote and on-site/hybrid positions."""
        remote_postings = list(
            db.scalars(
                select(JobPosting).where(
                    JobPosting.is_active.is_(True),
                    JobPosting.is_remote.is_(True),
                )
            ).all()
        )
        onsite_postings = list(
            db.scalars(
                select(JobPosting).where(
                    JobPosting.is_active.is_(True),
                    JobPosting.is_remote.is_(False),
                )
            ).all()
        )

        return {
            "remote": summarize_distribution(self._extract_midpoints(remote_postings)),
            "onsite": summarize_distribution(self._extract_midpoints(onsite_postings)),
        }

    def get_salary_for_skill(self, db: Session, skill_name: str) -> DistributionSummary:
        """Compute salary benchmarks for postings requiring a specific skill."""
        stmt = (
            select(JobPosting)
            .join(JobSkill, JobSkill.job_id == JobPosting.id)
            .join(Skill, Skill.id == JobSkill.skill_id)
            .where(
                JobPosting.is_active.is_(True),
                Skill.normalized_name == skill_name.strip().lower(),
            )
        )
        postings = list(db.scalars(stmt).all())
        return summarize_distribution(self._extract_midpoints(postings))


salary_analyzer = SalaryAnalyzer()
