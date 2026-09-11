"""Database engine and session management.

Configures connection pooling, session lifecycle, and connectivity helpers.
Supports SQLite (development/testing) and PostgreSQL (production).
"""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def get_engine_args(database_url: str) -> dict[str, Any]:
    """Return engine configuration arguments tailored to the database dialect."""
    connect_args: dict[str, Any] = {}
    engine_kwargs: dict[str, Any] = {
        "echo": settings.debug and settings.environment == "development",
        "future": True,
    }

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
    else:
        # PostgreSQL connection pool settings
        engine_kwargs.update(
            {
                "pool_size": 10,
                "max_overflow": 20,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
            }
        )

    return engine_kwargs


def create_db_engine(database_url: str | None = None) -> Engine:
    """Create and return a configured SQLAlchemy Engine instance."""
    url = database_url or settings.database_url
    engine_kwargs = get_engine_args(url)
    return create_engine(url, **engine_kwargs)


# Application-level engine singleton
engine: Engine = create_db_engine()

# Configured sessionmaker factory
SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for standalone database session lifecycle management.

    Ensures transactions are committed on success, rolled back on error,
    and sessions are cleanly closed.
    """
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping_database(db_engine: Engine | None = None) -> bool:
    """Execute a simple query to verify database connectivity.

    Returns True if database is reachable, raises or returns False otherwise.
    """
    target_engine = db_engine or engine
    with target_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return result.scalar() == 1
