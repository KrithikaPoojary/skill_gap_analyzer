"""Experience tier classification service.

Infers seniority levels (entry, mid, senior, lead) from job titles,
text descriptions, and explicit years-of-experience requirements.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from app.schemas.enums import ExperienceLevel


class ClassificationResult(NamedTuple):
    """Result of seniority tier classification."""

    level: ExperienceLevel
    confidence: float
    detected_years: int | None
    matched_keyword: str | None


class ExperienceClassifier:
    """Classifies job postings into standard seniority levels."""

    YEARS_REGEX = re.compile(
        r"(\d+)\s*(?:\+|-\s*\d+)?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)",
        re.IGNORECASE,
    )

    TITLE_TIER_RULES: list[tuple[list[str], ExperienceLevel, float]] = [
        (["intern", "internship", "apprentice", "trainee"], ExperienceLevel.ENTRY, 0.95),
        (["junior", "jr", "entry level", "associate", "graduate"], ExperienceLevel.ENTRY, 0.90),
        (["principal", "staff", "architect", "lead", "head", "director", "vp", "chief"], ExperienceLevel.LEAD, 0.90),
        (["senior", "sr", "tech lead"], ExperienceLevel.SENIOR, 0.85),
        (["mid-level", "intermediate"], ExperienceLevel.MID, 0.80),
    ]

    def extract_years_requirement(self, text: str) -> int | None:
        """Extract minimum years of experience required from raw text."""
        if not text:
            return None
        match = self.YEARS_REGEX.search(text)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                return None
        return None

    def classify_from_years(self, years: int) -> ExperienceLevel:
        """Map years of experience to standard seniority level."""
        if years <= 2:
            return ExperienceLevel.ENTRY
        elif years <= 5:
            return ExperienceLevel.MID
        elif years <= 8:
            return ExperienceLevel.SENIOR
        else:
            return ExperienceLevel.LEAD

    def classify(
        self,
        title: str,
        description: str = "",
        requirements: str = "",
    ) -> ClassificationResult:
        """Classify a job posting using title keywords and experience mentions."""
        title_lower = title.strip().lower()

        # 1. Check title signals first (strongest indicator)
        for keywords, tier, conf in self.TITLE_TIER_RULES:
            for kw in keywords:
                # Word boundary check for acronyms like 'sr' or 'jr'
                pattern = rf"\b{re.escape(kw)}\b"
                if re.search(pattern, title_lower):
                    years = self.extract_years_requirement(f"{requirements} {description}")
                    return ClassificationResult(
                        level=tier,
                        confidence=conf,
                        detected_years=years,
                        matched_keyword=kw,
                    )

        # 2. Check explicit years of experience in requirements and description
        full_text = f"{requirements} {description}".strip()
        years = self.extract_years_requirement(full_text)
        if years is not None:
            tier = self.classify_from_years(years)
            return ClassificationResult(
                level=tier,
                confidence=0.80,
                detected_years=years,
                matched_keyword=f"{years} years",
            )

        # 3. Default fallback to MID level
        return ClassificationResult(
            level=ExperienceLevel.MID,
            confidence=0.50,
            detected_years=None,
            matched_keyword=None,
        )


experience_classifier = ExperienceClassifier()
