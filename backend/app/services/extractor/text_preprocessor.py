"""Text normalization and n-gram tokenization preprocessor for skill extraction.

Prepares unstructured text for skill extraction by normalizing punctuation,
preserving tech identifiers (.NET, C++, Node.js), and generating n-grams.
"""

from __future__ import annotations

import re


class ExtractorTextPreprocessor:
    """Prepares and tokenizes raw job descriptions and resumes for skill extraction."""

    # Normalization regexes
    BULLET_REGEX = re.compile(r"^[\s*•\-–—►▪◦\d\.\)]+", re.MULTILINE)
    WHITESPACE_REGEX = re.compile(r"[ \t]+")
    NEWLINE_COLLAPSE = re.compile(r"\n{3,}")

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Clean raw text while preserving technology punctuations (+, #, ., /)."""
        if not text:
            return ""

        # Remove bullet markers at line starts
        cleaned = cls.BULLET_REGEX.sub("", text)
        # Collapse excessive newlines and whitespace
        cleaned = cls.NEWLINE_COLLAPSE.sub("\n\n", cleaned)
        cleaned = cls.WHITESPACE_REGEX.sub(" ", cleaned)
        return cleaned.strip()

    @classmethod
    def extract_ngrams(cls, text: str, max_n: int = 3) -> list[tuple[str, int, int]]:
        """Generate sliding n-grams (1 to max_n words) with character start/end offsets.

        Returns:
            List of (ngram_string, start_char_index, end_char_index).
        """
        # Find all word-like tokens including symbols like ++, #, ., /
        token_pattern = re.compile(r"[\w\+\#\./\-]+")
        matches = list(token_pattern.finditer(text))

        ngrams: list[tuple[str, int, int]] = []
        num_tokens = len(matches)

        for n in range(1, max_n + 1):
            for i in range(num_tokens - n + 1):
                start_match = matches[i]
                end_match = matches[i + n - 1]
                span_start = start_match.start()
                span_end = end_match.end()
                ngram_text = text[span_start:span_end].strip()
                ngrams.append((ngram_text, span_start, span_end))

        return ngrams


extractor_text_preprocessor = ExtractorTextPreprocessor()
