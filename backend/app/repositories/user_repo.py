"""User and Profile repository implementations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import Profile, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access repository for User entities."""

    def __init__(self) -> None:
        super().__init__(User)

    def get_by_email(self, db: Session, *, email: str) -> User | None:
        """Fetch user by case-insensitive unique email address."""
        stmt = select(User).where(User.email == email.strip().lower())
        return db.scalar(stmt)

    def get_active_users(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Fetch only active user records."""
        stmt = select(User).where(User.is_active.is_(True)).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())


user_repository = UserRepository()
