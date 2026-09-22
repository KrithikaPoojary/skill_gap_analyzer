"""User and Profile SQLAlchemy ORM models.

Models the core authentication entity (User) and the professional profile (Profile)
supporting resumes, links, experience levels, and career details.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.associations import UserSkill
    from app.models.role import UserTargetRole


class User(Base, TimestampMixin):
    """User account entity for authentication and profile association."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 1-to-1 relationship with Profile
    profile: Mapped[Profile | None] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 1-to-many relationship with UserSkill association
    user_skills: Mapped[list[UserSkill]] = relationship(
        "UserSkill",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # 1-to-many relationship with UserTargetRole association
    target_roles: Mapped[list[UserTargetRole]] = relationship(
        "UserTargetRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # 1-to-many relationship with Notification
    notifications: Mapped[list] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"


class Profile(Base, TimestampMixin):
    """Candidate profile containing professional metadata, links, and experience."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    years_of_experience: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationship back to User
    user: Mapped[User] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, user_id={self.user_id}, title='{self.current_title}')>"
