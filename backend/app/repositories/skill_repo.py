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


skill_repository = SkillRepository()
