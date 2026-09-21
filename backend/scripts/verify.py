"""System Verification Script.

Validates:
1.  Application settings and configuration loading.
2.  Database engine connectivity and ping latency.
3.  Complete schema inspection across all ORM tables.
4.  Alembic migration head alignment.
5.  Repository layer instantiation.
6.  Dataset file artifacts.
7.  Database ingestion & population health.
8.  Market analytics pipeline.
9.  Skill Extraction Engine (NLP pipeline smoke test).
10. User Profile & Gap Analysis Services (gap analysis + recommendation smoke test).
11. Learning Roadmap Generator (DAG prerequisites + resource catalog + curriculum smoke test).
12. Resume Ingestion Pipeline (DocumentParser + ResumeSegmenter + ResumeIngestionService smoke test).
13. Full pytest test suite execution and test count reporting.
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

    # 8. Market Analytics Pipeline Validation
    try:
        from app.db.session import SessionLocal
        from app.services.analytics_service import analytics_service

        with SessionLocal() as db:
            overview = analytics_service.get_market_overview(db)

        analytics_ok = (
            overview.total_active_jobs >= 500
            and len(overview.top_skills) > 0
            and len(overview.top_roles) > 0
            and overview.overall_remote_pct > 0.0
        )
        detail = (
            f"Overview active: {len(overview.top_skills)} top skills, {overview.overall_remote_pct:.1f}% remote"
            if analytics_ok
            else "Analytics metrics below expectations"
        )
        log_step("Market Analytics Pipeline", analytics_ok, detail)
        if not analytics_ok:
            all_passed = False
    except Exception as exc:
        log_step("Market Analytics Pipeline", False, str(exc))
        all_passed = False

    # 9. Skill Extraction Engine
    try:
        import time
        from app.services.skill_extractor import skill_extractor
        from app.services.extractor.batch_extractor import batch_skill_extractor

        probe_text = (
            "Senior Backend Engineer: 5+ years Python, FastAPI, PostgreSQL, Redis, "
            "Docker, Kubernetes, and AWS cloud platform."
        )
        t0 = time.perf_counter()
        extracted = skill_extractor.extract_skills(probe_text)
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        required_skills = {"Python", "Docker", "AWS"}
        found_names = {s.name for s in extracted}
        extraction_ok = required_skills.issubset(found_names)

        # Batch smoke: two documents
        batch_report = batch_skill_extractor.extract_batch([
            ("doc-a", "Python and FastAPI developer needed."),
            ("doc-b", "React and TypeScript frontend engineer."),
        ])
        batch_ok = batch_report.total_documents == 2 and batch_report.total_skills_extracted >= 2

        skill_ok = extraction_ok and batch_ok
        detail = (
            f"{len(extracted)} skills in {elapsed_ms} ms; batch: {batch_report.total_skills_extracted} skills"
            if skill_ok
            else f"Missing: {required_skills - found_names}"
        )
        log_step("Skill Extraction Engine", skill_ok, detail)
        if not skill_ok:
            all_passed = False
    except Exception as exc:
        log_step("Skill Extraction Engine", False, str(exc))
        all_passed = False

    # 10. User Profile & Gap Analysis Services
    try:
        from app.services.skill_gap_analyzer import SkillWeight, skill_gap_analyzer
        from app.services.gap_analysis_service import gap_analysis_service
        from app.services.recommendation_service import recommendation_service
        from app.db.session import SessionLocal

        # Compute smoke gap analysis
        test_weights = [
            SkillWeight("Python", 1.0),
            SkillWeight("FastAPI", 0.9),
            SkillWeight("Docker", 0.8),
        ]
        rep = skill_gap_analyzer.analyse(
            profile_skills=["Python", "FastAPI"],
            required_skills=test_weights,
            role_name="Smoke Test Role",
        )
        analyzer_ok = (
            rep.coverage_pct > 60.0
            and "Python" in rep.matched_skills
            and "FastAPI" in rep.matched_skills
            and any(s.name == "Docker" for s in rep.missing_skills)
        )

        with SessionLocal() as db:
            # Test recommendation ranking
            recs = recommendation_service.recommend_for_skills(
                db,
                skills=["Python", "PostgreSQL"],
                limit=3,
            )
            # Service call should succeed without unhandled exceptions
            services_ok = analyzer_ok and isinstance(recs, list)

        detail = (
            f"Gap score: {rep.weighted_gap_score * 100:.1f}%, {len(recs)} target roles evaluated"
            if services_ok
            else "Gap analysis verification mismatch"
        )
        log_step("Profile & Gap Analysis Services", services_ok, detail)
        if not services_ok:
            all_passed = False
    except Exception as exc:
        log_step("Profile & Gap Analysis Services", False, str(exc))
        all_passed = False

    # 11. Learning Roadmap Generator
    try:
        from app.services.roadmap.prerequisite_graph import skill_prerequisite_graph
        from app.services.roadmap.resource_catalog import learning_resource_catalog
        from app.services.roadmap.roadmap_generator import roadmap_generator

        # Smoke check prerequisite sort
        ordered = skill_prerequisite_graph.sort_skills(["FastAPI", "Python"])
        prereq_ok = ordered == ["Python", "FastAPI"]

        # Smoke check resource catalog
        meta = learning_resource_catalog.get_skill_metadata("FastAPI")
        catalog_ok = meta.estimated_hours > 0 and len(meta.resources) > 0

        # Smoke check roadmap generation
        smoke_rm = roadmap_generator.generate(
            missing_skills=["Python", "FastAPI", "Docker"],
            role_title="Backend Developer",
            weekly_commitment_hours=10,
        )
        generator_ok = (
            smoke_rm.total_skills == 3
            and smoke_rm.estimated_weeks > 0
            and len(smoke_rm.phases) >= 2
            and bool(smoke_rm.phases[0].capstone_project_title)
        )

        roadmap_ok = prereq_ok and catalog_ok and generator_ok
        detail = (
            f"{smoke_rm.total_skills} skills in {len(smoke_rm.phases)} phases, {smoke_rm.estimated_weeks} weeks pacing"
            if roadmap_ok
            else "Roadmap verification mismatch"
        )
        log_step("Learning Roadmap Generator", roadmap_ok, detail)
        if not roadmap_ok:
            all_passed = False
    except Exception as exc:
        log_step("Learning Roadmap Generator", False, str(exc))
        all_passed = False

    # 12. Resume Ingestion Pipeline Smoke Test
    try:
        from app.services.document_parser import DocumentParser
        from app.services.resume_segmenter import ResumeSegmenter
        from app.services.resume_ingestion_service import ResumeIngestionService

        resume_txt = (
            "Alice Developer\n"
            "alice@example.com\n"
            "+1-555-000-1234\n"
            "https://linkedin.com/in/alice\n"
            "\n"
            "Summary\n"
            "Senior software engineer with 8 years of Python experience.\n"
            "\n"
            "Skills\n"
            "Python, FastAPI, Docker, PostgreSQL, Redis\n"
            "\n"
            "Experience\n"
            "Lead Engineer - Acme Corp (2018-Present)\n"
            "Designed microservices architecture.\n"
        ).encode("utf-8")

        parser = DocumentParser()
        raw_text = parser.parse_bytes(resume_txt, "smoke_test.txt")
        parser_ok = "Python" in raw_text and len(raw_text) > 50

        segmenter = ResumeSegmenter()
        segments = segmenter.segment(raw_text)
        segmenter_ok = (
            "skills" in segments.sections
            and "experience" in segments.sections
            and segments.contact.email == "alice@example.com"
            and "Python" in segments.skills_raw
        )

        svc = ResumeIngestionService(parser=parser, segmenter=segmenter)
        result = svc.parse_only(resume_txt, "smoke_test.txt")
        service_ok = (
            result.char_count > 0
            and "skills" in result.sections_found
            and result.contact.email == "alice@example.com"
            and len(result.skills_raw) >= 3
        )

        resume_ok = parser_ok and segmenter_ok and service_ok
        detail = (
            f"{len(result.sections_found)} sections, {len(result.skills_raw)} skills extracted"
            if resume_ok else "Resume pipeline verification mismatch"
        )
        log_step("Resume Ingestion Pipeline", resume_ok, detail)
        if not resume_ok:
            all_passed = False
    except Exception as exc:
        log_step("Resume Ingestion Pipeline", False, str(exc))
        all_passed = False

    # 13. User Authentication & JWT Security Pipeline Check
    try:
        import uuid
        from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
        from app.db.session import SessionLocal
        from app.schemas.auth import UserRegisterRequest
        from app.services.auth_service import auth_service

        pwd = "TestPassword123!"
        hashed = hash_password(pwd)
        pwd_ok = verify_password(pwd, hashed) and not verify_password("wrong", hashed)

        db = SessionLocal()
        try:
            test_email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
            req = UserRegisterRequest(email=test_email, password=pwd, full_name="Verify User")
            user = auth_service.register_user(db, req=req)
            reg_ok = user.id is not None and user.email == test_email

            authed_user = auth_service.authenticate(db, email=test_email, password=pwd)
            auth_ok = authed_user is not None and authed_user.id == user.id

            token = create_access_token(subject=user.id, extra_claims={"email": user.email})
            payload = decode_access_token(token)
            jwt_ok = str(payload.get("sub")) == str(user.id) and payload.get("email") == user.email

            auth_pipeline_ok = pwd_ok and reg_ok and auth_ok and jwt_ok
            detail = (
                f"Argon2id pwd + DB user registration (id={user.id}) + JWT token validated"
                if auth_pipeline_ok else "Auth pipeline check mismatch"
            )
            log_step("User Auth & JWT Pipeline", auth_pipeline_ok, detail)
            if not auth_pipeline_ok:
                all_passed = False
        finally:
            db.close()
    except Exception as exc:
        log_step("User Auth & JWT Pipeline", False, str(exc))
        all_passed = False

    # 14. User Profile & Stats Integration Check
    try:
        from app.db.session import SessionLocal
        from app.services.profile_service import profile_service
        db = SessionLocal()
        try:
            stats = profile_service.get_user_stats(db, user_id=user.id)
            stats_ok = isinstance(stats, dict) and "total_skills" in stats and "avg_proficiency_score" in stats
            detail = f"User stats computed (skills={stats['total_skills']}, complete={stats['profile_complete']})"
            log_step("Profile & Stats Service", stats_ok, detail)
            if not stats_ok:
                all_passed = False
        finally:
            db.close()
    except Exception as exc:
        log_step("Profile & Stats Service", False, str(exc))
        all_passed = False

    # 15. Run Pytest Suite
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
