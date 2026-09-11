"""Target roles, benchmark skill weightings, and user target career models.

Enables calculating readiness scores, benchmark skill thresholds, and gap roadmaps.
"""

from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.user import User


class TargetRole(Base, TimestampMixin):
    """A benchmark IT career profile against which user skill gaps are evaluated."""

    __tablename__ = "target_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50),
        default="Software Engineering",
        nullable=False,
    )
    min_experience_years: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    role_skills: Mapped[list[RoleSkillWeighting]] = relationship(
        "RoleSkillWeighting",
        back_populates="role",
        cascade="all, delete-orphan",
    )
    user_associations: Mapped[list[UserTargetRole]] = relationship(
        "UserTargetRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TargetRole(id={self.id}, title='{self.title}', category='{self.category}')>"


class RoleSkillWeighting(Base, TimestampMixin):
    """Benchmark weighting and proficiency expectation for a skill in a target role."""

    __tablename__ = "role_skill_weightings"

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("target_roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )  # 1.0 to 5.0 scale importance
    is_core: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )  # Core vs optional skill
    benchmark_level: Mapped[str] = mapped_column(
        String(50),
        default="intermediate",
        nullable=False,
    )  # beginner, intermediate, advanced, expert

    # Relationships
    role: Mapped[TargetRole] = relationship("TargetRole", back_populates="role_skills")
    skill: Mapped[Skill] = relationship("Skill", back_populates="role_skills")

    def __repr__(self) -> str:
        return (
            f"<RoleSkillWeighting(role_id={self.role_id}, skill_id={self.skill_id}, "
            f"weight={self.weight}, is_core={self.is_core})>"
        )


class UserTargetRole(Base, TimestampMixin):
    """Associates a User with an aspirational career target role."""

    __tablename__ = "user_target_roles"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("target_roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    target_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="target_roles")
    role: Mapped[TargetRole] = relationship("TargetRole", back_populates="user_associations")

    def __repr__(self) -> str:
        return (
            f"<UserTargetRole(user_id={self.user_id}, role_id={self.role_id}, "
            f"score={self.readiness_score})>"
        )
