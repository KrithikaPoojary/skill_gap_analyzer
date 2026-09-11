"""Generic SQLAlchemy repository base providing standard CRUD operations.

Follows the Repository Pattern to decouple data access logic from
business services and API route handlers.
"""

from typing import Any, Generic, TypeVar
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository implementing standard persistence operations."""

    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    def get(self, db: Session, entity_id: Any) -> ModelType | None:
        """Fetch a single record by primary key."""
        return db.get(self.model, entity_id)

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """Fetch multiple records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def count(self, db: Session) -> int:
        """Return the total number of records for the entity."""
        stmt = select(func.count()).select_from(self.model)
        return db.scalar(stmt) or 0

    def create(self, db: Session, *, obj_in: dict[str, Any] | ModelType) -> ModelType:
        """Persist a new entity record."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: dict[str, Any],
    ) -> ModelType:
        """Update fields of an existing entity record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, entity_id: Any) -> ModelType | None:
        """Remove an entity record by primary key."""
        obj = db.get(self.model, entity_id)
        if obj is not None:
            db.delete(obj)
            db.commit()
        return obj
