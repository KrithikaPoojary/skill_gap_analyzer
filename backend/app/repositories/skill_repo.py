"""Skill repository implementation."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.repositories.base import BaseRepository


class SkillRepository(BaseRepository[Skill]):
    """Data access repository for Skill entities."""

    def __init__(self) -> None:
        super().__init__(Skill)

    def get_by_name(self, db: Session, *, name: str) -> Skill | None:
        """Fetch skill by exact name."""
        stmt = select(Skill).where(Skill.name == name)
        return db.scalar(stmt)

    def get_by_normalized_name(self, db: Session, *, normalized_name: str) -> Skill | None:
        """Fetch skill by sanitized/normalized name."""
        stmt = select(Skill).where(Skill.normalized_name == normalized_name)
        return db.scalar(stmt)

    def get_by_category(
        self,
        db: Session,
        *,
        category: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Skill]:
        """Fetch skills filtered by taxonomy category."""
        stmt = select(Skill).where(Skill.category == category).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def search(
        self,
        db: Session,
        *,
        query: str,
        limit: int = 20,
    ) -> list[Skill]:
        """Full-text ilike search on skill name."""
        stmt = (
            select(Skill)
            .where(Skill.name.ilike(f"%{query}%"))
            .order_by(Skill.name)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_category_stats(self, db: Session) -> list[dict]:
        """Return all taxonomy categories with the count of skills in each."""
        from sqlalchemy import func
        from app.models.skill import SkillCategory

        stmt = select(Skill.category, func.count(Skill.id)).group_by(Skill.category)
        counts = dict(db.execute(stmt).all())

        results = []
        for cat in SkillCategory:
            results.append({
                "category": cat.value,
                "label": cat.value.replace("_", " ").title(),
                "skill_count": counts.get(cat.value, 0),
            })
        return results

    def get_skill_demand_metrics(self, db: Session, *, skill_id: int) -> dict | None:
        """Fetch demand metrics for a specific skill across jobs, target roles, and users."""
        from sqlalchemy import func
        from app.models.associations import JobSkill, UserSkill
        from app.models.job import JobPosting
        from app.models.role import RoleSkillWeighting, TargetRole

        skill = db.get(Skill, skill_id)
        if not skill:
            return None

        # Count active job postings requiring this skill
        job_count_stmt = (
            select(func.count(JobSkill.job_id), func.avg(JobSkill.importance_weight))
            .join(JobPosting, JobSkill.job_id == JobPosting.id)
            .where(JobSkill.skill_id == skill_id, JobPosting.is_active.is_(True))
        )
        job_row = db.execute(job_count_stmt).one()
        active_jobs_count = job_row[0] or 0
        avg_weight = round(float(job_row[1]), 2) if job_row[1] is not None else 0.0

        # Count target roles requiring this skill
        role_stmt = (
            select(TargetRole.id, TargetRole.title, RoleSkillWeighting.is_core, RoleSkillWeighting.weight)
            .join(RoleSkillWeighting, TargetRole.id == RoleSkillWeighting.role_id)
            .where(RoleSkillWeighting.skill_id == skill_id, TargetRole.is_active.is_(True))
        )
        role_rows = db.execute(role_stmt).all()
        target_roles = [
            {
                "role_id": r[0],
                "role_title": r[1],
                "is_core": r[2],
                "weight": r[3],
            }
            for r in role_rows
        ]

        # Count candidates possessing this skill
        candidate_count = db.scalar(
            select(func.count(UserSkill.user_id)).where(UserSkill.skill_id == skill_id)
        ) or 0

        return {
            "skill_id": skill.id,
            "name": skill.name,
            "category": skill.category,
            "is_verified": skill.is_verified,
            "active_job_count": active_jobs_count,
            "avg_importance_weight": avg_weight,
            "target_roles_count": len(target_roles),
            "target_roles": target_roles,
            "candidates_count": candidate_count,
        }


skill_repository = SkillRepository()

