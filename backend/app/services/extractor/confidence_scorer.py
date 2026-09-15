"""Confidence scoring engine for extracted technical skills.

Scores candidate extractions based on match precision, document section location,
repetition frequency, and proximity to technical context keywords.
"""

from __future__ import annotations

import re

from app.services.extractor.pattern_engine import RawSkillMatch


class ConfidenceScorer:
    """Computes a normalized confidence rating (0.0 to 1.0) for extracted skill matches."""

    SECTION_HEADER_REGEX = re.compile(
        r"(?:requirements|qualifications|skills|technical stack|technologies|must have|preferred):?",
        re.IGNORECASE,
    )

    PROXIMITY_KEYWORD_REGEX = re.compile(
        r"\b(?:proficient|experience|hands-on|knowledge|expert|familiarity|strong|working with)\b",
        re.IGNORECASE,
    )

    def score_match(
        self,
        match: RawSkillMatch,
        full_text: str,
        total_occurrences: int = 1,
    ) -> float:
        """Calculate confidence score for a skill match within text."""
        # 1. Base score: exact canonical vs alias match
        is_exact = match.matched_text.lower() == match.canonical_name.lower()
        score = 0.90 if is_exact else 0.85

        # 2. Section context bonus
        window_start = max(0, match.start - 80)
        leading_text = full_text[window_start:match.start]
        if self.SECTION_HEADER_REGEX.search(leading_text):
            score += 0.08

        # 3. Proximity keyword bonus
        window_end = min(len(full_text), match.end + 40)
        surrounding_window = full_text[window_start:window_end]
        if self.PROXIMITY_KEYWORD_REGEX.search(surrounding_window):
            score += 0.05

        # 4. Multi-occurrence bonus (up to +0.06)
        if total_occurrences > 1:
            score += min(0.06, (total_occurrences - 1) * 0.03)

        return round(min(1.0, max(0.10, score)), 2)


confidence_scorer = ConfidenceScorer()
