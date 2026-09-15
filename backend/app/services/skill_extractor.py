"""Comprehensive skill extraction pipeline service.

Extracts technical skills from unstructured job descriptions or resumes,
deduplicates aliases to canonical taxonomy entries, and computes confidence scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.extractor.confidence_scorer import confidence_scorer
from app.services.extractor.pattern_engine import RawSkillMatch, skill_pattern_engine
from app.services.extractor.text_preprocessor import extractor_text_preprocessor

# Characters of surrounding context to capture per match occurrence
_SNIPPET_CONTEXT_CHARS = 60
_MAX_SNIPPETS = 3


def _extract_snippet(text: str, start: int, end: int) -> str:
    """Return a short surrounding context string for a match span."""
    s = max(0, start - _SNIPPET_CONTEXT_CHARS)
    e = min(len(text), end + _SNIPPET_CONTEXT_CHARS)
    snippet = text[s:e].strip()
    # Ellipsis when truncated
    if s > 0:
        snippet = "…" + snippet
    if e < len(text):
        snippet = snippet + "…"
    return snippet


@dataclass(frozen=True)
class ExtractedSkill:
    """Consolidated representation of an extracted technical skill."""

    name: str
    category: str
    confidence: float
    occurrences: int
    matched_variants: list[str]
    context_snippets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "confidence": self.confidence,
            "occurrences": self.occurrences,
            "matched_variants": self.matched_variants,
            "context_snippets": self.context_snippets,
        }


class SkillExtractor:
    """High-accuracy skill extraction pipeline with alias resolution and deduplication."""

    def extract_skills(
        self,
        text: str,
        *,
        min_confidence: float = 0.60,
    ) -> list[ExtractedSkill]:
        """Extract all technical skills from arbitrary text.

        Args:
            text: Unstructured input text (job posting description or resume).
            min_confidence: Minimum score threshold (0.0 to 1.0) to include a skill.

        Returns:
            Deduplicated list of ExtractedSkill objects sorted by confidence.
        """
        if not text or not text.strip():
            return []

        cleaned_text = extractor_text_preprocessor.normalize_text(text)
        raw_matches = skill_pattern_engine.find_matches(cleaned_text)

        if not raw_matches:
            return []

        # Group matches by canonical name
        grouped: dict[str, list[RawSkillMatch]] = {}
        for m in raw_matches:
            grouped.setdefault(m.canonical_name, []).append(m)

        extracted_results: list[ExtractedSkill] = []

        for canonical_name, match_list in grouped.items():
            first_match = match_list[0]
            occurrences = len(match_list)
            variants = list({m.matched_text for m in match_list})

            # Capture surrounding context for first N occurrences
            snippets = [
                _extract_snippet(cleaned_text, m.start, m.end)
                for m in match_list[:_MAX_SNIPPETS]
            ]

            # Calculate score using first match and total occurrences
            score = confidence_scorer.score_match(
                first_match,
                cleaned_text,
                total_occurrences=occurrences,
            )

            if score >= min_confidence:
                category_val = (
                    first_match.category.value
                    if hasattr(first_match.category, "value")
                    else str(first_match.category)
                )
                extracted_results.append(
                    ExtractedSkill(
                        name=canonical_name,
                        category=category_val,
                        confidence=score,
                        occurrences=occurrences,
                        matched_variants=variants,
                        context_snippets=snippets,
                    )
                )

        # Sort descending by confidence, then occurrence count
        extracted_results.sort(key=lambda s: (s.confidence, s.occurrences), reverse=True)
        return extracted_results


skill_extractor = SkillExtractor()
