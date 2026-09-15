"""Unit tests for the integrated SkillExtractor service."""

import pytest

from app.services.skill_extractor import ExtractedSkill, SkillExtractor, skill_extractor


class TestSkillExtractor:
    """Test suite for full text extraction, confidence ranking, and alias deduplication."""

    def test_extract_skills_from_job_description(self) -> None:
        text = """
        Job Title: Senior Backend Developer
        Requirements:
        • 5+ years of experience with Python and FastAPI
        • Strong knowledge of PostgreSQL and Redis
        • Experience deploying containerized applications with Docker on AWS
        • Good communication and problem solving skills
        """
        results = skill_extractor.extract_skills(text)
        assert len(results) >= 5

        names = {s.name for s in results}
        assert "Python" in names
        assert "FastAPI" in names
        assert "PostgreSQL" in names
        assert "Docker" in names
        assert "AWS" in names

        # Verify sorted by confidence descending
        confidences = [s.confidence for s in results]
        assert confidences == sorted(confidences, reverse=True)

    def test_alias_consolidation_and_frequency(self) -> None:
        text = "We use React and reactjs for frontend, along with k8s and Kubernetes."
        results = skill_extractor.extract_skills(text)

        names = [s.name for s in results]
        # Should be deduplicated to canonical names
        assert names.count("React") == 1
        assert names.count("Kubernetes") == 1

        react_skill = next(s for s in results if s.name == "React")
        assert react_skill.occurrences == 2
        assert set(react_skill.matched_variants) == {"React", "reactjs"}

    def test_empty_or_whitespace_text(self) -> None:
        assert skill_extractor.extract_skills("") == []
        assert skill_extractor.extract_skills("   \n\t  ") == []
