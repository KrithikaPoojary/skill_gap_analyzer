"""Unit tests for the SkillPatternEngine service."""

import pytest

from app.models.skill import SkillCategory
from app.services.extractor.pattern_engine import SkillPatternEngine, skill_pattern_engine


class TestSkillPatternEngine:
    """Test suite for compiled regex pattern matching across canonical terms and aliases."""

    def test_find_canonical_and_alias_matches(self) -> None:
        text = "We build APIs with FastAPI and Python, deploying on k8s with Docker."
        matches = skill_pattern_engine.find_matches(text)

        names = {m.canonical_name for m in matches}
        assert "FastAPI" in names
        assert "Python" in names
        assert "Kubernetes" in names  # 'k8s' resolved to Kubernetes
        assert "Docker" in names

    def test_multi_word_skill_recognition(self) -> None:
        text = "Looking for experts in Machine Learning, Deep Learning, and Spring Boot."
        matches = skill_pattern_engine.find_matches(text)

        names = {m.canonical_name for m in matches}
        assert "Machine Learning" in names
        assert "Deep Learning" in names
        assert "Spring Boot" in names

    def test_tricky_characters_plus_and_hash(self) -> None:
        text = "Backend stack includes C++, C#, .NET, and PostgreSQL."
        matches = skill_pattern_engine.find_matches(text)

        names = {m.canonical_name for m in matches}
        assert "C++" in names
        assert "C#" in names
        assert ".NET" in names
        assert "PostgreSQL" in names

    def test_avoids_false_positive_go_verb(self) -> None:
        text = "Candidates will go through our interview process and go live with code."
        matches = skill_pattern_engine.find_matches(text)
        names = {m.canonical_name for m in matches}
        assert "Go" not in names
