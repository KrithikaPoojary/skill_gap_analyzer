"""Database seeding script.

Idempotently seeds the development/test database with the curated
IT job market dataset (520+ jobs, 50+ skills, and ~2000 associations).

Usage:
    python scripts/seed_database.py
    python scripts/seed_database.py --force
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from sqlalchemy import select
from app.db.base import Base
from app.db.session import SessionLocal, engine
import app.models  # noqa: F401
from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill
from app.services.ingestion_service import ingestion_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed database with job market dataset.")
    parser.add_argument(
        "--dataset",
        type=str,
        default=os.path.join(backend_root, "data", "jobs_dataset.json"),
        help="Path to JSON dataset (defaults to data/jobs_dataset.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Seed even if database already contains records",
    )
    return parser.parse_args()


def seed_taxonomy_catalog(db) -> int:
    """Pre-seed the full canonical taxonomy skill catalog."""
    from app.services.skill_normalizer import TAXONOMY_CATALOG, skill_normalizer
    count = 0
    for item in TAXONOMY_CATALOG:
        skill_normalizer.resolve_or_create(db, item.canonical_name)
        count += 1
    db.commit()
    return count


def verify_seeding(db) -> bool:
    """Verify that expected minimum data volume is present."""
    job_count = db.query(JobPosting).count()
    skill_count = db.query(Skill).count()
    assoc_count = db.query(JobSkill).count()

    print("\nDatabase Population Check:")
    print(f"  - Job Postings:    {job_count:>5} (target: >= 500)")
    print(f"  - Skills Catalog:  {skill_count:>5} (target: >= 50)")
    print(f"  - Skill Links:     {assoc_count:>5} (target: >= 1500)")

    is_healthy = job_count >= 500 and skill_count >= 50 and assoc_count >= 1500
    status_label = "[OK] Dataset fully populated" if is_healthy else "[WARN] Data volume below targets"
    print(f"  {status_label}\n")
    return is_healthy


def main() -> int:
    args = parse_args()
    file_path = os.path.abspath(args.dataset)

    if not os.path.exists(file_path):
        print(f"Error: Dataset file not found at: {file_path}", file=sys.stderr)
        return 1

    # Ensure schema exists
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Pre-seed taxonomy skills
        seed_taxonomy_catalog(db)

        current_jobs = db.query(JobPosting).count()
        if current_jobs > 0 and not args.force:
            print(f"Database already contains {current_jobs} jobs. Use --force to re-run ingestion.")
            is_valid = verify_seeding(db)
            return 0 if is_valid else 1

        print(f"Seeding database from: {file_path}...")
        report = ingestion_service.ingest_json_file(db, file_path, batch_size=100)
        print(f"Ingestion complete: {report.inserted_records} inserted, {report.skipped_records} skipped, {report.error_records} errors in {report.duration_seconds}s.")

        is_valid = verify_seeding(db)
        return 0 if is_valid else 1

    except Exception as exc:
        print(f"Seeding failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
