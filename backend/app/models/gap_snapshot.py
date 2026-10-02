"""Skill gap analysis historical snapshot model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from sqlalchemy import Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.role import TargetRole
    from app.models.user import User


class SkillGapSnapshot(Base, TimestampMixin):
    """Historical record of candidate readiness evaluation against a target role."""

    __tablename__ = "skill_gap_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True
    )
    role_title: Mapped[str] = mapped_column(String(100), nullable=False)
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    matched_skills: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    missing_skills: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    user: Mapped[User] = relationship("User", backref="gap_snapshots")
    role: Mapped[TargetRole | None] = relationship("TargetRole")

    def __repr__(self) -> str:
        return (
            f"<SkillGapSnapshot(id={self.id}, user_id={self.user_id}, "
            f"role='{self.role_title}', score={self.readiness_score})>"
        )
