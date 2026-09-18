"""Unit tests for RoadmapGenerator."""

import pytest
from app.services.roadmap.roadmap_generator import (
    GeneratedRoadmap,
    RoadmapGenerator,
    roadmap_generator,
)


class TestRoadmapGenerator:
    def test_generate_roadmap_backend_role(self):
        missing = ["FastAPI", "Docker", "Python", "Kubernetes", "PostgreSQL"]
        roadmap = roadmap_generator.generate(
            missing_skills=missing,
            role_title="Backend Engineer",
            weekly_commitment_hours=10,
        )

        assert isinstance(roadmap, GeneratedRoadmap)
        assert roadmap.role_title == "Backend Engineer"
        assert roadmap.total_skills == 5
        assert roadmap.total_estimated_hours > 0
        assert roadmap.weekly_commitment_hours == 10
        assert roadmap.estimated_weeks > 0
        assert len(roadmap.phases) >= 2

        # Phase 1 should contain foundation skills (e.g. Python)
        phase_1_skills = [s.name for s in roadmap.phases[0].skills]
        assert "Python" in phase_1_skills

        # Phase 1 capstone project exists
        assert "Capstone" in roadmap.phases[0].capstone_project_title or "Foundations" in roadmap.phases[0].capstone_project_title
        assert len(roadmap.phases[0].capstone_project_description) > 10

    def test_generate_roadmap_empty_skills(self):
        roadmap = roadmap_generator.generate(
            missing_skills=[],
            role_title="Data Scientist",
        )
        assert roadmap.total_skills == 0
        assert roadmap.total_estimated_hours == 0
        assert roadmap.estimated_weeks == 0
        assert len(roadmap.phases) == 0

    def test_generate_roadmap_pacing_variation(self):
        skills = ["Python", "FastAPI", "Docker"]
        roadmap_slow = roadmap_generator.generate(
            missing_skills=skills,
            weekly_commitment_hours=5,
        )
        roadmap_fast = roadmap_generator.generate(
            missing_skills=skills,
            weekly_commitment_hours=20,
        )

        assert roadmap_slow.total_estimated_hours == roadmap_fast.total_estimated_hours
        assert roadmap_slow.estimated_weeks > roadmap_fast.estimated_weeks

    def test_generate_roadmap_deduplicates_skills(self):
        skills = ["Python", "python", "PYTHON", "FastAPI"]
        roadmap = roadmap_generator.generate(
            missing_skills=skills,
            role_title="API Dev",
        )
        assert roadmap.total_skills == 2

    def test_roadmap_to_dict_serialization(self):
        skills = ["TypeScript", "React", "Next.js"]
        roadmap = roadmap_generator.generate(
            missing_skills=skills,
            role_title="Frontend Developer",
            weekly_commitment_hours=15,
        )
        d = roadmap.to_dict()
        assert d["role_title"] == "Frontend Developer"
        assert d["total_skills"] == 3
        assert "phases" in d
        assert len(d["phases"]) > 0
        assert "skills" in d["phases"][0]
        assert "resources" in d["phases"][0]["skills"][0]
