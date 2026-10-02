"""Target role repository implementation."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models.role import RoleSkillWeighting, TargetRole, UserTargetRole
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[TargetRole]):
    """Data access repository for TargetRole entities."""

    def __init__(self) -> None:
        super().__init__(TargetRole)

    def get_by_slug(self, db: Session, *, slug: str) -> TargetRole | None:
        """Fetch target role by unique slug."""
        stmt = select(TargetRole).where(TargetRole.slug == slug)
        return db.scalar(stmt)

    def get_active_roles(
        self,
        db: Session,
        *,
        category: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[TargetRole]:
        """Fetch active target roles with optional category filtering."""
        stmt = select(TargetRole).where(TargetRole.is_active.is_(True))
        if category:
            stmt = stmt.where(TargetRole.category == category)
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_role_with_skills(self, db: Session, *, role_id: int) -> TargetRole | None:
        """Fetch target role with eager-loaded role skill weightings."""
        stmt = (
            select(TargetRole)
            .options(
                joinedload(TargetRole.role_skills).joinedload(RoleSkillWeighting.skill)
            )
            .where(TargetRole.id == role_id)
        )
        return db.scalar(stmt)

    def assign_user_target_role(
        self,
        db: Session,
        *,
        user_id: int,
        role_id: int,
        target_date: datetime | None = None,
    ) -> UserTargetRole:
        """Associate or update a user's target aspirational role."""
        stmt = select(UserTargetRole).where(
            UserTargetRole.user_id == user_id,
            UserTargetRole.role_id == role_id,
        )
        existing = db.scalar(stmt)
        if existing:
            if target_date is not None:
                existing.target_date = target_date
            db.commit()
            db.refresh(existing)
            return existing

        assoc = UserTargetRole(
            user_id=user_id,
            role_id=role_id,
            target_date=target_date,
            readiness_score=0.0,
        )
        db.add(assoc)
        db.commit()
        db.refresh(assoc)
        return assoc

    def get_user_target_roles(self, db: Session, *, user_id: int) -> list[UserTargetRole]:
        """Fetch all target roles tracked by a specific user with role details loaded."""
        stmt = (
            select(UserTargetRole)
            .options(joinedload(UserTargetRole.role))
            .where(UserTargetRole.user_id == user_id)
            .order_by(UserTargetRole.created_at.desc())
        )
        return list(db.scalars(stmt).unique().all())

    def remove_user_target_role(self, db: Session, *, user_id: int, role_id: int) -> bool:
        """Remove target role tracking for a user."""
        stmt = delete(UserTargetRole).where(
            UserTargetRole.user_id == user_id,
            UserTargetRole.role_id == role_id,
        )
        res = db.execute(stmt)
        db.commit()
        return bool(res.rowcount and res.rowcount > 0)


role_repository = RoleRepository()
