"""Ingestion telemetry and historical execution tracking.

Stores structured metrics for all dataset ingestion runs, providing observability
over batch ingestion counts, error rates, and throughput performance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class IngestionTelemetryRecord:
    """Individual record of a completed or failed ingestion run."""

    run_id: str
    source_name: str
    total_records: int
    inserted_records: int
    skipped_records: int
    error_records: int
    duration_seconds: float
    status: str  # 'success', 'partial', 'failed'
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IngestionTelemetryTracker:
    """Maintains an in-memory history of recent ingestion executions."""

    def __init__(self, max_history: int = 50) -> None:
        self._history: list[IngestionTelemetryRecord] = []
        self._max_history = max_history

    def record_run(
        self,
        run_id: str,
        source_name: str,
        total: int,
        inserted: int,
        skipped: int,
        errors: int,
        duration: float,
    ) -> IngestionTelemetryRecord:
        """Record a completed ingestion run."""
        if errors == 0:
            status = "success"
        elif inserted > 0:
            status = "partial"
        else:
            status = "failed"

        record = IngestionTelemetryRecord(
            run_id=run_id,
            source_name=source_name,
            total_records=total,
            inserted_records=inserted,
            skipped_records=skipped,
            error_records=errors,
            duration_seconds=round(duration, 3),
            status=status,
        )
        self._history.insert(0, record)
        if len(self._history) > self._max_history:
            self._history.pop()

        return record

    def get_recent(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve recent runs ordered by most recent first."""
        return [r.to_dict() for r in self._history[:limit]]

    def get_summary_stats(self) -> dict[str, Any]:
        """Compute aggregated statistics over all recorded runs."""
        total_runs = len(self._history)
        if total_runs == 0:
            return {
                "total_runs": 0,
                "total_inserted": 0,
                "total_skipped": 0,
                "total_errors": 0,
                "avg_duration_seconds": 0.0,
            }

        total_inserted = sum(r.inserted_records for r in self._history)
        total_skipped = sum(r.skipped_records for r in self._history)
        total_errors = sum(r.error_records for r in self._history)
        avg_dur = sum(r.duration_seconds for r in self._history) / total_runs

        return {
            "total_runs": total_runs,
            "total_inserted": total_inserted,
            "total_skipped": total_skipped,
            "total_errors": total_errors,
            "avg_duration_seconds": round(avg_dur, 3),
        }

    def clear(self) -> None:
        """Reset history."""
        self._history.clear()


ingestion_telemetry = IngestionTelemetryTracker()
