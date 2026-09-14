"""Skill frequency distribution and market penetration analyzer.

Analyzes job postings to compute skill demand frequency, category breakdowns,
penetration percentages, and mandatory-versus-preferred requirement ratios.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import Integer, case, cast, desc, func, select
from sqlalchemy.orm import Session

from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill, SkillCategory


@dataclass(frozen=True)
class SkillDemandRecord:
    """Statistical demand metrics for an individual skill."""

    skill_id: int
    skill_name: str
    category: str
    total_postings: int
    market_penetration_pct: float
    mandatory_count: int
    preferred_count: int
    avg_importance: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SkillAnalyzer:
    """Analyzes skill demand distributions across job postings."""

    def get_top_skills(
        self,
        db: Session,
        *,
        limit: int = 20,
        category: SkillCategory | None = None,
    ) -> list[SkillDemandRecord]:
        """Fetch top demanded skills ordered by job frequency."""
        total_jobs = db.scalar(
            select(func.count(JobPosting.id)).where(JobPosting.is_active.is_(True))
        ) or 0

        if total_jobs == 0:
            return []

        # Aggregation query
        stmt = (
            select(
                Skill.id,
                Skill.name,
                Skill.category,
                func.count(JobSkill.job_id).label("total_postings"),
                func.sum(case((JobSkill.is_required.is_(True), 1), else_=0)).label("mandatory_count"),
                func.avg(JobSkill.importance_weight).label("avg_importance"),
            )
            .join(JobSkill, Skill.id == JobSkill.skill_id)
            .join(JobPosting, JobPosting.id == JobSkill.job_id)
            .where(JobPosting.is_active.is_(True))
            .group_by(Skill.id, Skill.name, Skill.category)
        )

        if category:
            stmt = stmt.where(Skill.category == category.value)

        stmt = stmt.order_by(desc("total_postings")).limit(limit)
        rows = db.execute(stmt).all()

        records = []
        for row in rows:
            s_id, name, cat, total_p, mandatory_p, avg_imp = row
            mandatory_cnt = int(mandatory_p or 0)
            total_cnt = int(total_p or 0)
            preferred_cnt = total_cnt - mandatory_cnt
            penetration = round((total_cnt / total_jobs) * 100.0, 2)
            avg_weight = round(float(avg_imp or 1.0), 2)

            records.append(
                SkillDemandRecord(
                    skill_id=s_id,
                    skill_name=name,
                    category=cat,
                    total_postings=total_cnt,
                    market_penetration_pct=penetration,
                    mandatory_count=mandatory_cnt,
                    preferred_count=preferred_cnt,
                    avg_importance=avg_weight,
                )
            )

        return records

    def get_category_distribution(self, db: Session) -> dict[str, int]:
        """Compute aggregate skill requirement volume by skill category."""
        stmt = (
            select(
                Skill.category,
                func.count(JobSkill.job_id).label("demand_count"),
            )
            .join(JobSkill, Skill.id == JobSkill.skill_id)
            .join(JobPosting, JobPosting.id == JobSkill.job_id)
            .where(JobPosting.is_active.is_(True))
            .group_by(Skill.category)
            .order_by(desc("demand_count"))
        )
        rows = db.execute(stmt).all()
        return {r[0]: int(r[1]) for r in rows}


skill_analyzer = SkillAnalyzer()
