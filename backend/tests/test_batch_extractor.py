"""Unit tests for the BatchSkillExtractor service."""

import pytest

from app.services.extractor.batch_extractor import (
    BatchDocumentResult,
    BatchSkillExtractor,
    BatchSummaryReport,
    batch_skill_extractor,
)


class TestBatchSkillExtractor:
    """Test suite for batch text extraction, frequency aggregation, and error resilience."""

    def test_extract_batch_success(self) -> None:
        docs = [
            ("doc-1", "Hiring Python and FastAPI engineer."),
            ("doc-2", "Seeking frontend developer proficient in React and TypeScript."),
            ("doc-3", "Data scientist with Python, Pandas, and Machine Learning."),
        ]
        report = batch_skill_extractor.extract_batch(docs)

        assert report.total_documents == 3
        assert report.total_skills_extracted >= 6
        assert len(report.document_results) == 3
        assert report.total_duration_ms > 0

        # Verify aggregate frequency: Python appears in doc-1 and doc-3
        assert report.skill_frequency["Python"] == 2
        assert report.avg_skills_per_document > 1.0

    def test_extract_batch_empty_list(self) -> None:
        report = batch_skill_extractor.extract_batch([])
        assert report.total_documents == 0
        assert report.total_skills_extracted == 0
        assert report.avg_skills_per_document == 0.0
