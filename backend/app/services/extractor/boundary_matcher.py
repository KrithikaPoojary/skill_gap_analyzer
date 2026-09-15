"""Boundary pattern matcher and ambiguous term disambiguation service.

Prevents common false positives where short technical acronyms and language names
overlap with common English words (e.g., 'Go', 'C', 'R', 'AI', 'Rust').
"""

from __future__ import annotations

import re


class BoundaryMatcher:
    """Disambiguates ambiguous technical terms using contextual pattern rules."""

    # Programming contextual indicators
    TECH_INDICATORS = re.compile(
        r"\b(?:developer|engineer|programmer|backend|frontend|code|coding|software|language|programming|stack|written in|experience in|proficient with|proficient in|knowledge of|framework|library|runtime|pipeline)\b",
        re.IGNORECASE,
    )

    # Patterns for tricky terms
    GO_POSITIVE_PATTERNS = [
        re.compile(r"\bGo\s+(?:developer|engineer|backend|programming|language|code|routines|routines?)\b"),
        re.compile(r"\b(?:golang|go-lang)\b", re.IGNORECASE),
        re.compile(r"\b(?:Python|Java|C\+\+|Rust)[,\s/]+Go\b"),
        re.compile(r"\bGo[,\s/]+(?:Python|Java|C\+\+|Rust)\b"),
        re.compile(r"\b(?:proficient|experience)\s+(?:in|with)\s+Go\b"),
        re.compile(r"\bwritten\s+in\s+Go\b"),
    ]

    GO_NEGATIVE_PATTERNS = [
        re.compile(r"\bgo\s+(?:to|ahead|forward|beyond|through|back|live|deep)\b", re.IGNORECASE),
        re.compile(r"\bon\s+the\s+go\b", re.IGNORECASE),
        re.compile(r"\bgo-to\b", re.IGNORECASE),
        re.compile(r"\bgood\b", re.IGNORECASE),
    ]

    C_POSITIVE_PATTERNS = [
        re.compile(r"\bC\s*/\s*C\+\+(?:\s|[,\./]|$)"),
        re.compile(r"\bC\s+and\s+C\+\+(?:\s|[,\./]|$)"),
        re.compile(r"\bC\s+(?:programming|language|developer|engineer|embedded)\b"),
        re.compile(r"\bembedded\s+C\b", re.IGNORECASE),
        re.compile(r"\bC\s*,\s*C\+\+(?:\s|[,\./]|$)"),
    ]

    R_POSITIVE_PATTERNS = [
        re.compile(r"\bR\s+(?:programming|language|package|script|scripting)\b", re.IGNORECASE),
        re.compile(r"\bPython\s+and\s+R\b", re.IGNORECASE),
        re.compile(r"\b(?:Python|SQL)\s*[/,]\s*R\b", re.IGNORECASE),
        re.compile(r"\bR\s*[/,]\s*(?:Python|SQL)\b", re.IGNORECASE),
        re.compile(r"\bstatistics\s+with\s+R\b", re.IGNORECASE),
    ]

    def is_go_programming_match(self, text: str, match_span: tuple[int, int]) -> bool:
        """Verify if a match of 'Go' refers to Golang rather than common verb usage."""
        start, end = match_span
        matched_str = text[start:end]

        # Case sensitivity: 'go' lowercase is almost never programming language unless explicit 'golang'
        if matched_str == "go" and not text[start:start + 6].lower() == "golang":
            return False

        # Check negative phrases around match
        window_start = max(0, start - 30)
        window_end = min(len(text), end + 30)
        window = text[window_start:window_end]

        for neg in self.GO_NEGATIVE_PATTERNS:
            if neg.search(window):
                return False

        # Check positive indicators in window
        for pos in self.GO_POSITIVE_PATTERNS:
            if pos.search(window):
                return True

        # If capitalized 'Go' is surrounded by other technical terms
        if matched_str == "Go" and self.TECH_INDICATORS.search(window):
            return True

        return False

    def is_c_programming_match(self, text: str, match_span: tuple[int, int]) -> bool:
        """Verify if a match of 'C' refers to the C programming language."""
        start, end = match_span
        window_start = max(0, start - 25)
        window_end = min(len(text), end + 25)
        window = text[window_start:window_end]

        for pos in self.C_POSITIVE_PATTERNS:
            if pos.search(window):
                return True
        return False

    def is_r_programming_match(self, text: str, match_span: tuple[int, int]) -> bool:
        """Verify if a match of 'R' refers to the R statistical programming language."""
        start, end = match_span
        window_start = max(0, start - 25)
        window_end = min(len(text), end + 25)
        window = text[window_start:window_end]

        # Explicitly avoid R&D
        if "R&D" in window or "R & D" in window:
            return False

        for pos in self.R_POSITIVE_PATTERNS:
            if pos.search(window):
                return True
        return False


boundary_matcher = BoundaryMatcher()
