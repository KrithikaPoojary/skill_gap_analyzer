"""Unit tests for the IngestionTelemetryTracker service."""

import pytest

from app.services.ingestion_telemetry import IngestionTelemetryTracker


@pytest.fixture
def tracker():
    return IngestionTelemetryTracker(max_history=5)


class TestIngestionTelemetry:
    """Test suite for ingestion execution logging and statistical aggregation."""

    def test_record_run_success(self, tracker) -> None:
        rec = tracker.record_run("run-1", "test.json", 100, 100, 0, 0, 2.5)
        assert rec.status == "success"
        assert rec.inserted_records == 100

        recent = tracker.get_recent()
        assert len(recent) == 1
        assert recent[0]["run_id"] == "run-1"

    def test_record_run_partial_and_failed(self, tracker) -> None:
        rec_partial = tracker.record_run("run-2", "test.csv", 50, 40, 0, 10, 1.2)
        assert rec_partial.status == "partial"

        rec_failed = tracker.record_run("run-3", "bad.json", 10, 0, 0, 10, 0.5)
        assert rec_failed.status == "failed"

    def test_summary_stats(self, tracker) -> None:
        tracker.record_run("run-1", "test1.json", 100, 100, 0, 0, 2.0)
        tracker.record_run("run-2", "test2.json", 50, 40, 5, 5, 1.0)

        stats = tracker.get_summary_stats()
        assert stats["total_runs"] == 2
        assert stats["total_inserted"] == 140
        assert stats["total_skipped"] == 5
        assert stats["total_errors"] == 5
        assert stats["avg_duration_seconds"] == 1.5

    def test_max_history_limit(self, tracker) -> None:
        for i in range(10):
            tracker.record_run(f"run-{i}", "test.json", 10, 10, 0, 0, 0.1)

        recent = tracker.get_recent(limit=20)
        assert len(recent) == 5  # capped by max_history
        assert recent[0]["run_id"] == "run-9"
