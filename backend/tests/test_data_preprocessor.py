"""Unit tests for the DataPreprocessor service."""

import pytest

from app.services.data_preprocessor import DataPreprocessor, data_preprocessor


class TestDataPreprocessor:
    """Test suite for HTML stripping, unicode normalization, and deduplication hashing."""

    def test_clean_text_strips_html_and_unescapes(self) -> None:
        raw_html = "<p>We are hiring a <strong>Python Developer</strong> &amp; FastAPI engineer.</p>"
        cleaned = data_preprocessor.clean_text(raw_html)
        assert cleaned == "We are hiring a Python Developer & FastAPI engineer."

    def test_clean_text_collapses_whitespace(self) -> None:
        raw = "  Line 1   \n\n\t  Line 2   "
        cleaned = data_preprocessor.clean_text(raw)
        assert cleaned == "Line 1 Line 2"

    def test_clean_text_handles_none_and_empty(self) -> None:
        assert data_preprocessor.clean_text(None) == ""
        assert data_preprocessor.clean_text("   ") == ""

    def test_strip_urls(self) -> None:
        text = "Apply online at https://example.com/apply for details."
        assert data_preprocessor.strip_urls(text) == "Apply online at  for details."

    def test_generate_fingerprint_deterministic_and_case_insensitive(self) -> None:
        fp1 = data_preprocessor.generate_fingerprint("Senior Python Engineer", "Acme Corp", "Remote")
        fp2 = data_preprocessor.generate_fingerprint("  senior python engineer ", "ACME CORP", "remote")
        assert fp1 == fp2

    def test_truncate_summary(self) -> None:
        long_text = "This is a very long job description that outlines all the engineering responsibilities in great detail."
        summary = data_preprocessor.truncate_summary(long_text, max_chars=40)
        assert len(summary) <= 43
        assert summary.endswith("...")
