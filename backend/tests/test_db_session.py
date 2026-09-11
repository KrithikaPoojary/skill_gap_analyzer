"""Unit tests for database engine and session factory."""

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.base import Base, TimestampMixin, utc_now
from app.db.session import (
    create_db_engine,
    get_db_session,
    get_engine_args,
    ping_database,
)


class TestDatabaseFactory:
    """Test suite for engine creation, dialect args, and session context manager."""

    def test_engine_args_for_sqlite(self) -> None:
        args = get_engine_args("sqlite:///./test.db")
        assert "connect_args" in args
        assert args["connect_args"].get("check_same_thread") is False

    def test_engine_args_for_postgres(self) -> None:
        args = get_engine_args("postgresql://user:pass@localhost:5432/testdb")
        assert "pool_size" in args
        assert args["pool_size"] == 10
        assert args.get("pool_pre_ping") is True

    def test_create_db_engine_in_memory(self) -> None:
        mem_engine = create_db_engine("sqlite:///:memory:")
        assert isinstance(mem_engine, Engine)
        assert ping_database(mem_engine) is True

    def test_ping_database_success(self) -> None:
        mem_engine = create_db_engine("sqlite:///:memory:")
        assert ping_database(mem_engine) is True

    def test_get_db_session_context_manager(self) -> None:
        with get_db_session() as session:
            assert isinstance(session, Session)
            result = session.execute(text("SELECT 42"))
            assert result.scalar() == 42

    def test_base_and_timestamp_mixin(self) -> None:
        assert hasattr(TimestampMixin, "created_at")
        assert hasattr(TimestampMixin, "updated_at")
        now = utc_now()
        assert now.tzinfo is not None
