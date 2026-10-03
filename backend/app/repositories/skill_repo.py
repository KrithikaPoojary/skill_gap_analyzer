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


skill_repository = SkillRepository()
