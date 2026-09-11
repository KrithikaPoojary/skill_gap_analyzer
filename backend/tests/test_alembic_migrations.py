"""Unit tests for Alembic database migration configuration and schema completeness."""

import os
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db.base import Base
import app.models  # noqa: F401


class TestAlembicConfiguration:
    """Test suite verifying Alembic migrations and table definitions."""

    def test_alembic_ini_and_script_directory(self) -> None:
        ini_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
        assert os.path.isfile(ini_path)

        config = Config(ini_path)
        script_dir = ScriptDirectory.from_config(config)
        heads = script_dir.get_heads()
        assert len(heads) == 1, "Expected exactly 1 migration head in baseline"

    def test_all_expected_tables_registered_in_metadata(self) -> None:
        expected_tables = {
            "users",
            "profiles",
            "job_postings",
            "skills",
            "job_skills",
            "user_skills",
            "target_roles",
            "role_skill_weightings",
            "user_target_roles",
        }
        registered_tables = set(Base.metadata.tables.keys())
        assert expected_tables.issubset(registered_tables), (
            f"Missing tables: {expected_tables - registered_tables}"
        )
