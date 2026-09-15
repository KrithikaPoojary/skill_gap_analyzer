"""Unit tests for the ExtractorTextPreprocessor service."""

import pytest

from app.services.extractor.text_preprocessor import (
    ExtractorTextPreprocessor,
    extractor_text_preprocessor,
)


class TestExtractorPreprocessor:
    """Test suite for text cleaning, punctuation preservation, and n-gram generation."""

    def test_normalize_text_strips_bullets(self) -> None:
        raw = """
        • Strong proficiency in Python
        * Experience with Docker and Kubernetes
        1. Knowledge of CI/CD pipelines
        """
        cleaned = extractor_text_preprocessor.normalize_text(raw)
        assert "•" not in cleaned
        assert "*" not in cleaned
        assert "Strong proficiency in Python" in cleaned

    def test_normalize_text_preserves_tech_punctuations(self) -> None:
        raw = "We use C++, C#, .NET Core, Node.js, and CI/CD."
        cleaned = extractor_text_preprocessor.normalize_text(raw)
        assert "C++" in cleaned
        assert "C#" in cleaned
        assert ".NET Core" in cleaned
        assert "Node.js" in cleaned
        assert "CI/CD" in cleaned

    def test_extract_ngrams_spans(self) -> None:
        text = "React Spring Boot PostgreSQL"
        ngrams = extractor_text_preprocessor.extract_ngrams(text, max_n=2)

        # 1-grams: React, Spring, Boot, PostgreSQL
        # 2-grams: React Spring, Spring Boot, Boot PostgreSQL
        ngram_texts = [item[0] for item in ngrams]
        assert "React" in ngram_texts
        assert "Spring Boot" in ngram_texts
        assert "PostgreSQL" in ngram_texts

        # Verify exact character offsets
        sb_item = next(item for item in ngrams if item[0] == "Spring Boot")
        start, end = sb_item[1], sb_item[2]
        assert text[start:end] == "Spring Boot"
