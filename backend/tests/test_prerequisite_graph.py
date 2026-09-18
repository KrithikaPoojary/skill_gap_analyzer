"""Unit tests for SkillPrerequisiteGraph."""

import pytest
from app.services.roadmap.prerequisite_graph import (
    SkillPrerequisiteGraph,
    skill_prerequisite_graph,
)


class TestSkillPrerequisiteGraph:
    def test_direct_prerequisites_lookup(self):
        prereqs = skill_prerequisite_graph.get_direct_prerequisites("FastAPI")
        assert "python" in prereqs

        k8s_prereqs = skill_prerequisite_graph.get_direct_prerequisites("Kubernetes")
        assert "docker" in k8s_prereqs
        assert "linux" in k8s_prereqs

    def test_transitive_prerequisites(self):
        # Kubernetes depends on Docker, Docker depends on Linux
        all_prereqs = skill_prerequisite_graph.get_all_prerequisites("Kubernetes")
        assert "docker" in all_prereqs
        assert "linux" in all_prereqs

        assert skill_prerequisite_graph.has_prerequisite("Kubernetes", "Linux")
        assert skill_prerequisite_graph.has_prerequisite("Kubernetes", "Docker")
        assert not skill_prerequisite_graph.has_prerequisite("Docker", "Kubernetes")

    def test_topological_sort_backend_stack(self):
        # Input in arbitrary order: FastAPI, Docker, Python, Kubernetes, Linux
        unordered = ["Kubernetes", "FastAPI", "Docker", "Python", "Linux"]
        ordered = skill_prerequisite_graph.sort_skills(unordered)

        # In ordered list:
        # Python before FastAPI
        # Linux before Docker
        # Docker before Kubernetes
        pos = {s: i for i, s in enumerate(ordered)}
        assert pos["Python"] < pos["FastAPI"]
        assert pos["Linux"] < pos["Docker"]
        assert pos["Docker"] < pos["Kubernetes"]

    def test_topological_sort_frontend_stack(self):
        unordered = ["Next.js", "React", "HTML", "TypeScript", "JavaScript", "CSS"]
        ordered = skill_prerequisite_graph.sort_skills(unordered)
        pos = {s: i for i, s in enumerate(ordered)}

        assert pos["JavaScript"] < pos["TypeScript"]
        assert pos["JavaScript"] < pos["React"]
        assert pos["HTML"] < pos["React"]
        assert pos["React"] < pos["Next.js"]

    def test_group_into_dependency_levels(self):
        # Level 0: Python, SQL
        # Level 1: FastAPI, PostgreSQL
        skills = ["FastAPI", "Python", "PostgreSQL", "SQL"]
        levels = skill_prerequisite_graph.group_into_dependency_levels(skills)

        assert len(levels) >= 2
        level_0 = set(levels[0])
        level_1 = set(levels[1])

        assert "Python" in level_0
        assert "SQL" in level_0
        assert "FastAPI" in level_1
        assert "PostgreSQL" in level_1

    def test_cycle_tolerance(self):
        # Graph with cyclic definitions should not freeze or raise
        cyclic_graph = SkillPrerequisiteGraph(
            custom_prerequisites={
                "A": ("B",),
                "B": ("C",),
                "C": ("A",),
            }
        )
        sorted_skills = cyclic_graph.sort_skills(["A", "B", "C"])
        assert len(sorted_skills) == 3
        assert set(sorted_skills) == {"A", "B", "C"}

    def test_empty_input(self):
        assert skill_prerequisite_graph.sort_skills([]) == []
        assert skill_prerequisite_graph.group_into_dependency_levels([]) == []

    def test_add_custom_prerequisite(self):
        graph = SkillPrerequisiteGraph()
        graph.add_prerequisite("LangChain", "Python")
        graph.add_prerequisite("LangGraph", "LangChain")

        ordered = graph.sort_skills(["LangGraph", "LangChain", "Python"])
        assert ordered == ["Python", "LangChain", "LangGraph"]
