"""Job dataset batch ingestion and preprocessing pipeline service.

Handles loading, cleaning, deduplication, skill resolution, and persistence
of IT market job postings from JSON and CSV sources.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
import json
import logging
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import JobPosting
from app.schemas.enums import EmploymentType, ExperienceLevel, SourcePlatform
from app.schemas.job import JobCreate
from app.schemas.skill import JobSkillCreate
from app.services.job_service import job_service
from app.services.skill_normalizer import skill_normalizer

logger = logging.getLogger(__name__)


@dataclass
class IngestionReport:
    """Summary metrics of a dataset ingestion execution."""

    total_records: int = 0
    inserted_records: int = 0
    skipped_records: int = 0
    error_records: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary representation."""
        return asdict(self)


class IngestionService:
    """Pipeline for ingesting raw job market postings into the database."""

    def __init__(self) -> None:
        pass

    def _build_dedup_cache(self, db: Session) -> set[tuple[str, str, str]]:
        """Pre-populate a set of existing (title, company_name, location) tuples."""
        stmt = select(JobPosting.title, JobPosting.company_name, JobPosting.location)
        results = db.execute(stmt).all()
        return {
            (
                (r[0] or "").strip().lower(),
                (r[1] or "").strip().lower(),
                (r[2] or "").strip().lower(),
            )
            for r in results
        }

    def _clean_record(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Normalize whitespace, nulls, and types for a raw dictionary record."""
        cleaned: dict[str, Any] = {}
        for k, v in raw.items():
            if isinstance(v, str):
                cleaned[k] = v.strip()
            else:
                cleaned[k] = v

        # Default values and type fallbacks
        cleaned["is_remote"] = bool(cleaned.get("is_remote", False))
        cleaned["is_active"] = bool(cleaned.get("is_active", True))

        # Safe enum values
        emp_type = str(cleaned.get("employment_type", "full_time")).lower()
        if emp_type not in {e.value for e in EmploymentType}:
            emp_type = EmploymentType.FULL_TIME.value
        cleaned["employment_type"] = emp_type

        exp_level = str(cleaned.get("experience_level", "mid")).lower()
        if exp_level not in {e.value for e in ExperienceLevel}:
            exp_level = ExperienceLevel.MID.value
        cleaned["experience_level"] = exp_level

        platform = str(cleaned.get("source_platform", "manual")).lower()
        if platform not in {p.value for p in SourcePlatform}:
            platform = SourcePlatform.MANUAL.value
        cleaned["source_platform"] = platform

        # Numeric salary conversions
        for salary_field in ("min_salary", "max_salary"):
            val = cleaned.get(salary_field)
            if val is not None and val != "":
                try:
                    cleaned[salary_field] = float(val)
                except (ValueError, TypeError):
                    cleaned[salary_field] = None
            else:
                cleaned[salary_field] = None

        # Ensure min_salary <= max_salary
        if cleaned["min_salary"] and cleaned["max_salary"]:
            if cleaned["min_salary"] > cleaned["max_salary"]:
                cleaned["min_salary"], cleaned["max_salary"] = (
                    cleaned["max_salary"],
                    cleaned["min_salary"],
                )

        return cleaned

    def _resolve_skills(
        self,
        db: Session,
        raw_record: dict[str, Any],
    ) -> list[JobSkillCreate]:
        """Extract and resolve skill requirements attached to the record."""
        skill_payloads: list[JobSkillCreate] = []

        # Case 1: Structured list of skill dicts or string names
        raw_skills = raw_record.get("skills")
        if isinstance(raw_skills, list):
            for item in raw_skills:
                if isinstance(item, dict):
                    skill_name = str(item.get("name", "")).strip()
                    is_req = bool(item.get("is_required", True))
                    weight = float(item.get("importance_weight", 1.0))
                elif isinstance(item, str):
                    skill_name = item.strip()
                    is_req = True
                    weight = 1.0
                else:
                    continue

                if not skill_name:
                    continue

                skill = skill_normalizer.resolve_or_create(db, skill_name)
                skill_payloads.append(
                    JobSkillCreate(
                        skill_id=skill.id,
                        is_required=is_req,
                        importance_weight=weight,
                    )
                )

        # Case 2: Comma-separated skills string (common in CSV)
        skills_str = raw_record.get("skills_str")
        if isinstance(skills_str, str) and skills_str.strip():
            for name in skills_str.split(","):
                clean_name = name.strip()
                if not clean_name:
                    continue
                skill = skill_normalizer.resolve_or_create(db, clean_name)
                skill_payloads.append(
                    JobSkillCreate(
                        skill_id=skill.id,
                        is_required=True,
                        importance_weight=1.0,
                    )
                )

        return skill_payloads

    def ingest_records(
        self,
        db: Session,
        records: list[dict[str, Any]],
        *,
        batch_size: int = 50,
        dry_run: bool = False,
    ) -> IngestionReport:
        """Process and ingest a collection of job posting records.

        Args:
            db: Database session.
            records: List of raw job postings.
            batch_size: Transaction commit batch size.
            dry_run: If True, validate and simulate without persisting.

        Returns:
            IngestionReport with detailed execution statistics.
        """
        start_time = time.perf_counter()
        report = IngestionReport(total_records=len(records))
        dedup_cache = self._build_dedup_cache(db)

        for idx, raw in enumerate(records):
            try:
                cleaned = self._clean_record(raw)
                title = cleaned.get("title", "")
                company = cleaned.get("company_name", "")
                loc = cleaned.get("location") or ""

                if not title or not company:
                    report.error_records += 1
                    report.errors.append({
                        "index": idx,
                        "error": "Missing mandatory title or company_name",
                    })
                    continue

                dedup_key = (title.lower(), company.lower(), loc.lower())
                if dedup_key in dedup_cache:
                    report.skipped_records += 1
                    continue

                # Resolve skill requirements via taxonomy service
                skill_reqs = self._resolve_skills(db, cleaned)
                cleaned["skills"] = [s.model_dump() for s in skill_reqs]

                # Validate with JobCreate schema
                job_payload = JobCreate(**cleaned)

                if not dry_run:
                    job_service.create(db, payload=job_payload)

                dedup_cache.add(dedup_key)
                report.inserted_records += 1

                # Periodic batch commit
                if not dry_run and (idx + 1) % batch_size == 0:
                    db.commit()

            except Exception as exc:
                db.rollback()
                logger.error("Error ingesting record %d: %s", idx, exc)
                report.error_records += 1
                report.errors.append({
                    "index": idx,
                    "title": raw.get("title", "<unknown>"),
                    "error": str(exc),
                })

        if dry_run:
            db.rollback()
        else:
            db.commit()

        report.duration_seconds = round(time.perf_counter() - start_time, 3)
        logger.info(
            "Ingestion completed: %d total, %d inserted, %d skipped, %d errors in %.2fs",
            report.total_records,
            report.inserted_records,
            report.skipped_records,
            report.error_records,
            report.duration_seconds,
        )
        return report

    def ingest_json_file(
        self,
        db: Session,
        file_path: str,
        *,
        batch_size: int = 50,
        dry_run: bool = False,
    ) -> IngestionReport:
        """Load and ingest postings from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError(f"Expected list of job postings in JSON file, got {type(data).__name__}")

        return self.ingest_records(db, data, batch_size=batch_size, dry_run=dry_run)

    def ingest_csv_file(
        self,
        db: Session,
        file_path: str,
        *,
        batch_size: int = 50,
        dry_run: bool = False,
    ) -> IngestionReport:
        """Load and ingest postings from a CSV file."""
        records = []
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))

        return self.ingest_records(db, records, batch_size=batch_size, dry_run=dry_run)


ingestion_service = IngestionService()
