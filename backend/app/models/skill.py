"""Skill entity and taxonomy SQLAlchemy ORM model.

Defines individual technical and soft skills, category taxonomy,
normalized names for search/matching, and aliases.
"""

from __future__ import annotations
import enum
from sqlalchemy import Boolean, Enum as SQLEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SkillCategory(str, enum.Enum):
    """Categorical classification for IT and engineering skills."""

    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD_DEVOPS = "cloud_devops"
    AI_ML = "ai_ml"
    TESTING = "testing"
    METHODOLOGY = "methodology"
    SOFT_SKILL = "soft_skill"
    OTHER = "other"


class Skill(Base, TimestampMixin):
    """Skill taxonomy entity representing a distinct verifiable technical competence."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    normalized_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        default=SkillCategory.OTHER.value,
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aliases: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )  # Comma-separated alternative names/spellings
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @classmethod
    def normalize(cls, raw_name: str) -> str:
        """Standardize a skill name string for uniform matching and deduplication."""
        return raw_name.strip().lower().replace("-", " ").replace(".", "")

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}', category='{self.category}')>"
