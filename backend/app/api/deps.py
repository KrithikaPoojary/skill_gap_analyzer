"""FastAPI route dependencies.

Provides reusable dependency providers for database sessions, authentication,
and common query parameters.
"""

from collections.abc import Generator
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Provide an isolated database session per request.

    Ensures transactions are closed cleanly after request processing.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Type alias for cleaner endpoint signatures
DbSession = Annotated[Session, Depends(get_db)]
