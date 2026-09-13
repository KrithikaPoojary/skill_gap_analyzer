"""Data cleaning, text normalization, and deduplication preprocessor.

Cleans raw descriptions, removes HTML/markup noise, normalizes unicode characters,
and produces deterministic fingerprint hashes for duplicate detection.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata


class DataPreprocessor:
    """Sanitizes raw text content and provides deduplication hashing."""

    # Strip HTML tags
    TAG_REGEX = re.compile(r"<[^>]+>")
    # Collapse consecutive whitespace
    WHITESPACE_REGEX = re.compile(r"\s+")
    # URLs in raw text
    URL_REGEX = re.compile(r"https?://\S+|www\.\S+")

    @classmethod
    def clean_text(cls, raw: str | None) -> str:
        """Sanitize raw text by stripping HTML, normalizing unicode, and collapsing spaces."""
        if not raw:
            return ""

        # Unescape HTML entities (&amp; -> &, &lt; -> <, etc.)
        text = html.unescape(raw)
        # Remove HTML markup tags
        text = cls.TAG_REGEX.sub(" ", text)
        # Normalize unicode (replace curved quotes, dashes, etc.)
        text = unicodedata.normalize("NFKD", text)
        # Replace non-breaking spaces
        text = text.replace("\xa0", " ")
        # Collapse multiple whitespace
        text = cls.WHITESPACE_REGEX.sub(" ", text).strip()
        return text

    @classmethod
    def strip_urls(cls, text: str) -> str:
        """Remove URLs from text descriptions."""
        return cls.URL_REGEX.sub("", text).strip()

    @classmethod
    def generate_fingerprint(
        cls,
        title: str,
        company_name: str,
        location: str | None = None,
    ) -> str:
        """Generate a deterministic SHA-256 fingerprint for deduplication.

        Normalizes case and whitespace before hashing.
        """
        norm_title = cls.clean_text(title).lower()
        norm_company = cls.clean_text(company_name).lower()
        norm_loc = cls.clean_text(location or "").lower()

        composite = f"{norm_title}|{norm_company}|{norm_loc}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()

    @classmethod
    def truncate_summary(cls, text: str, max_chars: int = 250) -> str:
        """Extract a clean summary sentence up to max_chars."""
        cleaned = cls.clean_text(text)
        if len(cleaned) <= max_chars:
            return cleaned
        # Truncate at nearest word boundary
        truncated = cleaned[:max_chars].rsplit(" ", 1)[0]
        return f"{truncated}..."


data_preprocessor = DataPreprocessor()
