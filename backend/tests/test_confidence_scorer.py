"""Unit tests for the ConfidenceScorer service."""

import pytest

from app.models.skill import SkillCategory
from app.services.extractor.confidence_scorer import ConfidenceScorer, confidence_scorer
from app.services.extractor.pattern_engine import RawSkillMatch


class TestConfidenceScorer:
    """Test suite for match scoring, section boost, and frequency bonuses."""

    def test_exact_canonical_base_score(self) -> None:
        text = "Looking for a Python developer."
        match = RawSkillMatch(
            canonical_name="Python",
            category=SkillCategory.LANGUAGE,
            matched_text="Python",
            start=text.index("Python"),
            end=text.index("Python") + 6,
        )
        score = confidence_scorer.score_match(match, text, total_occurrences=1)
        assert score >= 0.90

    def test_section_and_proximity_boost(self) -> None:
        text = "Requirements: Must have hands-on experience with Python."
        match = RawSkillMatch(
            canonical_name="Python",
            category=SkillCategory.LANGUAGE,
            matched_text="Python",
            start=text.index("Python"),
            end=text.index("Python") + 6,
        )
        score = confidence_scorer.score_match(match, text, total_occurrences=2)
        # Should receive base (0.90) + section (0.08) + proximity (0.05) + multi-occurrence (0.03) capped at 1.0
        assert score == 1.0

    def test_alias_score(self) -> None:
        text = "Experience with k8s clusters."
        match = RawSkillMatch(
            canonical_name="Kubernetes",
            category=SkillCategory.CLOUD_DEVOPS,
            matched_text="k8s",
            start=text.index("k8s"),
            end=text.index("k8s") + 3,
        )
        score = confidence_scorer.score_match(match, text, total_occurrences=1)
        assert score >= 0.85
