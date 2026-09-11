"""Many-to-many association models for Jobs-Skills and Users-Skills.

Enriches raw link tables with contextual attributes such as requirement
flags, importance weights, proficiency levels, and verification status.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.job import JobPosting
    from app.models.skill import Skill
    from app.models.user import User


class JobSkill(Base, TimestampMixin):
    """Associative entity linking a JobPosting to required/preferred Skills."""

    __tablename__ = "job_skills"

    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_postings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )  # True: mandatory, False: nice-to-have
    importance_weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )  # 1.0 to 5.0 scale for match scoring

    # Relationships
    job: Mapped[JobPosting] = relationship("JobPosting", back_populates="job_skills")
    skill: Mapped[Skill] = relationship("Skill", back_populates="job_skills")

    def __repr__(self) -> str:
        return (
            f"<JobSkill(job_id={self.job_id}, skill_id={self.skill_id}, "
            f"is_required={self.is_required}, weight={self.importance_weight})>"
        )


class UserSkill(Base, TimestampMixin):
    """Associative entity linking a User to their claimed and verified Skills."""

    __tablename__ = "user_skills"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    proficiency_level: Mapped[str] = mapped_column(
        String(50),
        default="intermediate",
        nullable=False,
    )  # beginner, intermediate, advanced, expert
    years_of_experience: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="user_skills")
    skill: Mapped[Skill] = relationship("Skill", back_populates="user_skills")

    def __repr__(self) -> str:
        return (
            f"<UserSkill(user_id={self.user_id}, skill_id={self.skill_id}, "
            f"level='{self.proficiency_level}', verified={self.is_verified})>"
        )
