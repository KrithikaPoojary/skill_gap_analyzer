"""Pattern matching engine for technical skill recognition.

Compiles high-performance regex patterns across taxonomy skills and aliases,
coordinating with boundary matchers for ambiguous single-character keywords.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

from app.models.skill import SkillCategory
from app.services.extractor.boundary_matcher import boundary_matcher
from app.services.skill_normalizer import TAXONOMY_CATALOG, SkillDefinition, normalize_text


@dataclass(frozen=True)
class RawSkillMatch:
    """Raw pattern hit within text."""

    canonical_name: str
    category: SkillCategory
    matched_text: str
    start: int
    end: int


class SkillPatternEngine:
    """Pattern matching engine for finding canonical skills and aliases in text."""

    AMBIGUOUS_TERMS = {"go", "c", "r"}

    def __init__(self, catalog: Sequence[SkillDefinition] | None = None) -> None:
        self.catalog = catalog or TAXONOMY_CATALOG
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> list[tuple[SkillDefinition, list[re.Pattern]]]:
        """Compile regexes for each skill definition and all its aliases."""
        compiled = []
        for item in self.catalog:
            patterns = []
            # Canonical name
            patterns.append(self._make_pattern(item.canonical_name))
            # Aliases
            for alias in item.aliases:
                patterns.append(self._make_pattern(alias))
            compiled.append((item, patterns))
        return compiled

    def _make_pattern(self, term: str) -> re.Pattern:
        """Create a boundary-safe regular expression for a skill term."""
        clean = term.strip()
        escaped = re.escape(clean)

        # Handle terms ending in non-word symbols like ++, #, .
        left_bound = r"\b" if re.match(r"^\w", clean) else r"(?:^|\s|[,\./(])"
        right_bound = r"\b" if re.search(r"\w$", clean) else r"(?:\s|[,\./\)]|$)"

        pattern_str = rf"{left_bound}{escaped}{right_bound}"
        # Case insensitive unless ambiguous (Go, C, R)
        if clean.lower() in self.AMBIGUOUS_TERMS:
            return re.compile(pattern_str)  # Case-sensitive for Go, C, R
        return re.compile(pattern_str, re.IGNORECASE)

    def find_matches(self, text: str) -> list[RawSkillMatch]:
        """Scan text and return all raw skill matches with span offsets."""
        matches: list[RawSkillMatch] = []
        seen_spans: set[tuple[int, int]] = set()

        for defn, pattern_list in self._compiled_patterns:
            for pat in pattern_list:
                for m in pat.finditer(text):
                    span = (m.start(), m.end())
                    matched_slice = text[m.start():m.end()].strip()

                    # Disambiguate short/ambiguous terms
                    lower_clean = normalize_text(matched_slice)
                    if lower_clean == "go":
                        if not boundary_matcher.is_go_programming_match(text, span):
                            continue
                    elif lower_clean == "c":
                        if not boundary_matcher.is_c_programming_match(text, span):
                            continue
                    elif lower_clean == "r":
                        if not boundary_matcher.is_r_programming_match(text, span):
                            continue

                    # Avoid redundant overlapping sub-matches
                    if span in seen_spans:
                        continue
                    seen_spans.add(span)

                    matches.append(
                        RawSkillMatch(
                            canonical_name=defn.canonical_name,
                            category=defn.category,
                            matched_text=matched_slice,
                            start=m.start(),
                            end=m.end(),
                        )
                    )

        # Sort matches by appearance in text
        matches.sort(key=lambda x: x.start)
        return matches


skill_pattern_engine = SkillPatternEngine()
