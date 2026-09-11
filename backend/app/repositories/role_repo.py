"""Target role repository implementation."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import TargetRole
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


role_repository = RoleRepository()
