"""Dataset Ingestion CLI Runner.

Provides a command-line interface to batch-ingest IT job market postings
from JSON or CSV into the application database with telemetry and error tracking.

Usage:
    python scripts/ingest_jobs.py --dataset data/jobs_dataset.json
    python scripts/ingest_jobs.py --dataset data/jobs_dataset.csv --batch-size 100
    python scripts/ingest_jobs.py --dataset data/jobs_dataset.json --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.db.base import Base
from app.db.session import SessionLocal, engine
import app.models  # noqa: F401
from app.services.ingestion_service import IngestionReport, ingestion_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest job market dataset into database.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=os.path.join(backend_root, "data", "jobs_dataset.json"),
        help="Path to JSON or CSV dataset file (defaults to data/jobs_dataset.json)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch commit size (default: 50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and simulate ingestion without persisting changes",
    )
    return parser.parse_args()


def print_summary(report: IngestionReport, dry_run: bool) -> None:
    mode_label = "[DRY RUN - No changes written]" if dry_run else "[LIVE INGESTION]"
    print("\n" + "=" * 60)
    print(f"  DATASET INGESTION SUMMARY {mode_label}")
    print("=" * 60)
    print(f"  Total records in file:   {report.total_records}")
    print(f"  Successfully inserted:   {report.inserted_records}")
    print(f"  Duplicates skipped:      {report.skipped_records}")
    print(f"  Errors encountered:      {report.error_records}")
    print(f"  Execution duration:      {report.duration_seconds:.2f}s")
    print("=" * 60)

    if report.errors:
        print("\nTop Errors (first 5):")
        for err in report.errors[:5]:
            print(f"  - Record #{err.get('index', '?')}: {err.get('error')}")
        print()


def main() -> int:
    args = parse_args()
    file_path = os.path.abspath(args.dataset)

    if not os.path.exists(file_path):
        print(f"Error: Dataset file not found at: {file_path}", file=sys.stderr)
        return 1

    print(f"Starting ingestion from: {file_path}")
    print(f"Batch size: {args.batch_size} | Dry Run: {args.dry_run}")

    # Ensure all tables exist before ingestion
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if file_path.endswith(".json"):
            report = ingestion_service.ingest_json_file(
                db,
                file_path,
                batch_size=args.batch_size,
                dry_run=args.dry_run,
            )
        elif file_path.endswith(".csv"):
            report = ingestion_service.ingest_csv_file(
                db,
                file_path,
                batch_size=args.batch_size,
                dry_run=args.dry_run,
            )
        else:
            print(f"Error: Unsupported file format '{file_path}'. Must be .json or .csv", file=sys.stderr)
            return 1

        print_summary(report, args.dry_run)
        return 0 if report.error_records == 0 else 1

    except Exception as exc:
        print(f"Fatal ingestion failure: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
