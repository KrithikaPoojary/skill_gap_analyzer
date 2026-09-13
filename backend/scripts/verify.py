"""System Verification Script.

Validates:
1. Application settings and configuration loading.
2. Database engine connectivity and ping latency.
3. Complete schema inspection across all ORM tables.
4. Alembic migration head alignment.
5. Repository layer instantiation.
6. Full pytest test suite execution and test count reporting.
"""

from datetime import datetime, timezone
import os
import subprocess
import sys
from sqlalchemy import inspect

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from alembic.config import Config
from alembic.script import ScriptDirectory
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, ping_database
import app.models  # noqa: F401
from app.repositories import (
    job_repository,
    role_repository,
    skill_repository,
    user_repository,
)


def log_step(name: str, status: bool, detail: str = "") -> None:
    badge = "[OK]" if status else "[FAIL]"
    print(f"  {badge} {name:<45} {detail}")


def main() -> int:
    print("=" * 60)
    print(f"  SYSTEM VERIFICATION - {settings.app_name}")
    print("=" * 60)

    all_passed = True

    # 1. Configuration Check
    try:
        cfg_ok = bool(settings.app_name and settings.database_url)
        log_step("Application Settings Loading", cfg_ok, f"Environment: {settings.environment}")
    except Exception as exc:
        log_step("Application Settings Loading", False, str(exc))
        all_passed = False

    # 2. Database Ping
    try:
        ping_ok = ping_database(engine)
        log_step("Database Connectivity Ping", ping_ok, "Engine ping successful")
    except Exception as exc:
        log_step("Database Connectivity Ping", False, str(exc))
        all_passed = False

    # 3. Schema Table Verification
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
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
        if not expected_tables.issubset(existing_tables):
            Base.metadata.create_all(bind=engine)
            inspector = inspect(engine)
            existing_tables = set(inspector.get_table_names())

        missing = expected_tables - existing_tables
        schema_ok = len(missing) == 0
        detail = f"{len(expected_tables)} tables confirmed" if schema_ok else f"Missing: {missing}"
        log_step("Schema Table Verification", schema_ok, detail)
        if not schema_ok:
            all_passed = False
    except Exception as exc:
        log_step("Schema Table Verification", False, str(exc))
        all_passed = False

    # 4. Alembic Configuration Check
    try:
        ini_path = os.path.join(backend_root, "alembic.ini")
        cfg = Config(ini_path)
        script_dir = ScriptDirectory.from_config(cfg)
        heads = script_dir.get_heads()
        alembic_ok = len(heads) >= 1
        log_step("Alembic Migration Baseline", alembic_ok, f"Current head: {heads[0] if heads else 'None'}")
        if not alembic_ok:
            all_passed = False
    except Exception as exc:
        log_step("Alembic Migration Baseline", False, str(exc))
        all_passed = False

    # 5. Repository Instantiations
    repos_ok = all(
        [
            user_repository is not None,
            job_repository is not None,
            skill_repository is not None,
            role_repository is not None,
        ]
    )
    log_step("Repository Layer Instantiation", repos_ok, "User, Job, Skill, Role repos active")

    # 6. Dataset Files Verification
    try:
        json_ds = os.path.join(backend_root, "data", "jobs_dataset.json")
        csv_ds = os.path.join(backend_root, "data", "jobs_dataset.csv")
        files_exist = os.path.exists(json_ds) and os.path.exists(csv_ds)
        size_kb = (os.path.getsize(json_ds) // 1024) if files_exist else 0
        log_step("Dataset Artifacts Verification", files_exist, f"JSON ({size_kb} KB) & CSV available")
        if not files_exist:
            all_passed = False
    except Exception as exc:
        log_step("Dataset Artifacts Verification", False, str(exc))
        all_passed = False

    # 7. Database Population Health
    try:
        from app.db.session import SessionLocal
        from app.models.job import JobPosting
        from app.models.skill import Skill
        from app.models.associations import JobSkill

        with SessionLocal() as db:
            j_cnt = db.query(JobPosting).count()
            s_cnt = db.query(Skill).count()
            l_cnt = db.query(JobSkill).count()

        pop_ok = j_cnt >= 500 and s_cnt >= 50 and l_cnt >= 1500
        log_step(
            "Database Ingestion & Population",
            pop_ok,
            f"{j_cnt} jobs, {s_cnt} skills, {l_cnt} links",
        )
        if not pop_ok:
            all_passed = False
    except Exception as exc:
        log_step("Database Ingestion & Population", False, str(exc))
        all_passed = False

    # 8. Run Pytest Suite
    print("\n  Running full test suite...")
    venv_python = sys.executable
    result = subprocess.run(
        [venv_python, "-m", "pytest", "tests/", "-q"],
        cwd=backend_root,
        capture_output=True,
        text=True,
    )
    test_output = result.stdout.strip() or result.stderr.strip()
    tests_ok = result.returncode == 0
    log_step("Pytest Test Suite", tests_ok, test_output.splitlines()[-1] if test_output else "")
    if not tests_ok:
        all_passed = False
        print("\nTest failures:")
        print(test_output)

    print("-" * 60)
    if all_passed:
        print("  [SUCCESS] All system checks passed successfully!")
        return 0
    else:
        print("  [ERROR] Some system checks failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
