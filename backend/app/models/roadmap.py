"""Learning Roadmap and Milestone ORM models.

Enables saving personalized learning curricula, tracking progress through
progressive milestone phases, and validating capstone project outcomes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.role import TargetRole
    from app.models.skill import Skill
    from app.models.user import User


class LearningRoadmap(Base, TimestampMixin):
    """A personalized, multi-phase curriculum for bridging skill deficits."""

    __tablename__ = "learning_roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    target_role_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("target_roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    target_role_name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_skills: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_estimated_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weekly_commitment_hours: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    estimated_weeks: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # active, completed, archived

    # Relationships
    milestones: Mapped[list[RoadmapMilestone]] = relationship(
        "RoadmapMilestone",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapMilestone.order_index",
    )
    user: Mapped[User | None] = relationship("User", foreign_keys=[user_id])
    target_role: Mapped[TargetRole | None] = relationship("TargetRole", foreign_keys=[target_role_id])

    def __repr__(self) -> str:
        return f"<LearningRoadmap(id={self.id}, title='{self.title}', weeks={self.estimated_weeks})>"


class RoadmapMilestone(Base, TimestampMixin):
    """A sequential stage/phase within a learning roadmap."""

    __tablename__ = "roadmap_milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    roadmap_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("learning_roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase_number: Mapped[int] = mapped_column(Integer, nullable=False)
    phase_title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capstone_project_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    capstone_project_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_phase_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_weeks: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    roadmap: Mapped[LearningRoadmap] = relationship("LearningRoadmap", back_populates="milestones")
    skills: Mapped[list[MilestoneSkill]] = relationship(
        "MilestoneSkill",
        back_populates="milestone",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<RoadmapMilestone(id={self.id}, phase={self.phase_number}, title='{self.phase_title}')>"


class MilestoneSkill(Base, TimestampMixin):
    """An individual technical skill tracked within a roadmap milestone."""

    __tablename__ = "milestone_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    milestone_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roadmap_milestones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="intermediate", nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    milestone: Mapped[RoadmapMilestone] = relationship("RoadmapMilestone", back_populates="skills")
    skill: Mapped[Skill | None] = relationship("Skill", foreign_keys=[skill_id])

    def __repr__(self) -> str:
        return f"<MilestoneSkill(id={self.id}, name='{self.skill_name}', completed={self.is_completed})>"
