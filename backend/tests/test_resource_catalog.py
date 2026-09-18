"""Unit tests for LearningResourceCatalog."""

import pytest
from app.services.roadmap.resource_catalog import (
    LearningResourceCatalog,
    learning_resource_catalog,
)


class TestLearningResourceCatalog:
    def test_catalog_lookup_known_skill(self):
        meta = learning_resource_catalog.get_skill_metadata("FastAPI")
        assert meta.skill_name == "FastAPI"
        assert meta.difficulty == "intermediate"
        assert meta.estimated_hours == 20
        assert len(meta.resources) > 0
        assert meta.resources[0].resource_type in {"official_docs", "course", "interactive"}

    def test_catalog_case_insensitive_lookup(self):
        meta_upper = learning_resource_catalog.get_skill_metadata("DOCKER")
        meta_lower = learning_resource_catalog.get_skill_metadata("docker")
        assert meta_upper.skill_name == "Docker"
        assert meta_upper.estimated_hours == meta_lower.estimated_hours

    def test_catalog_uncataloged_fallback(self):
        meta = learning_resource_catalog.get_skill_metadata("CustomRareFramework")
        assert meta.skill_name == "CustomRareFramework"
        assert meta.estimated_hours > 0
        assert meta.difficulty == "intermediate"
        assert len(meta.resources) == 1
        assert "documentation" in meta.resources[0].url.lower()

    def test_total_estimated_hours(self):
        # Python (30) + FastAPI (20) + Docker (18) = 68 hours
        skills = ["Python", "FastAPI", "Docker"]
        total = learning_resource_catalog.get_total_estimated_hours(skills)
        assert total == 30 + 20 + 18

    def test_resource_to_dict_serialization(self):
        meta = learning_resource_catalog.get_skill_metadata("PostgreSQL")
        d = meta.to_dict()
        assert d["skill_name"] == "PostgreSQL"
        assert isinstance(d["resources"], list)
        assert "url" in d["resources"][0]
        assert "is_free" in d["resources"][0]
