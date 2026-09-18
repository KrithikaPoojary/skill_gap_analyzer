"""Skill Prerequisite Graph Engine.

Models technical competencies as a Directed Acyclic Graph (DAG), resolving
skill prerequisites, calculating transitive dependencies, and computing
topologically ordered learning sequences.
"""

from __future__ import annotations

from collections import deque
from typing import Sequence


def _norm(name: str) -> str:
    """Standardize skill name for graph lookups matching Skill.normalize."""
    return " ".join(name.strip().lower().replace("-", " ").replace(".", "").split())


class SkillPrerequisiteGraph:
    """Directed Acyclic Graph representing technical skill prerequisites."""

    # Default prerequisite rules: canonical_skill -> tuple of immediate prerequisites
    DEFAULT_PREREQUISITES: dict[str, tuple[str, ...]] = {
        # Backend & Python Ecosystem
        "fastapi": ("python",),
        "flask": ("python",),
        "django": ("python", "sql"),
        "celery": ("python", "redis"),
        "sqlalchemy": ("python", "sql"),
        # AI / ML / Data Science
        "pandas": ("python",),
        "numpy": ("python",),
        "scikit learn": ("python", "numpy", "pandas"),
        "pytorch": ("python", "numpy"),
        "tensorflow": ("python", "numpy"),
        "keras": ("python", "tensorflow"),
        "nlp": ("python", "scikit learn"),
        "transformers": ("python", "pytorch"),
        "bert": ("python", "pytorch", "nlp"),
        "computer vision": ("python", "numpy"),
        "opencv": ("python", "numpy"),
        # Frontend & Web
        "typescript": ("javascript",),
        "react": ("javascript", "html", "css"),
        "nextjs": ("react", "javascript", "typescript"),
        "next js": ("react", "javascript", "typescript"),
        "vue": ("javascript", "html", "css"),
        "angular": ("typescript", "html", "css"),
        "nodejs": ("javascript",),
        "node js": ("javascript",),
        "express": ("nodejs", "javascript"),
        "tailwind css": ("css", "html"),
        "sass": ("css",),
        "redux": ("react", "javascript"),
        # Cloud & DevOps
        "docker": ("linux",),
        "kubernetes": ("docker", "linux"),
        "helm": ("kubernetes", "docker"),
        "terraform": ("cloud computing", "linux"),
        "ansible": ("linux", "python"),
        "ci cd": ("git", "linux"),
        "jenkins": ("linux", "git", "ci cd"),
        "github actions": ("git", "ci cd"),
        "aws": ("linux", "networking"),
        "azure": ("cloud computing", "networking"),
        "gcp": ("linux", "cloud computing"),
        # Databases & Messaging
        "postgresql": ("sql",),
        "mysql": ("sql",),
        "redis": ("linux",),
        "kafka": ("distributed systems", "linux"),
        "rabbitmq": ("linux", "networking"),
        "mongodb": ("nosql",),
        "elasticsearch": ("linux", "json"),
        # Mobile
        "react native": ("react", "javascript"),
        "flutter": ("dart",),
        "swiftui": ("swift",),
        "xcode": ("swift",),
    }

    def __init__(
        self,
        custom_prerequisites: dict[str, Sequence[str]] | None = None,
    ) -> None:
        self._prereqs: dict[str, tuple[str, ...]] = {}
        # Load defaults
        for skill, prereqs in self.DEFAULT_PREREQUISITES.items():
            self._prereqs[_norm(skill)] = tuple(_norm(p) for p in prereqs)

        # Merge custom
        if custom_prerequisites:
            for skill, prereqs in custom_prerequisites.items():
                self._prereqs[_norm(skill)] = tuple(_norm(p) for p in prereqs)

    def add_prerequisite(self, skill: str, prerequisite: str) -> None:
        """Register a new prerequisite edge: skill depends on prerequisite."""
        s = _norm(skill)
        p = _norm(prerequisite)
        existing = self._prereqs.get(s, ())
        if p not in existing:
            self._prereqs[s] = existing + (p,)

    def get_direct_prerequisites(self, skill: str) -> list[str]:
        """Return direct prerequisites for a skill."""
        return list(self._prereqs.get(_norm(skill), ()))

    def get_all_prerequisites(self, skill: str) -> set[str]:
        """Return all transitive prerequisites (ancestors) for a skill."""
        visited: set[str] = set()
        queue: deque[str] = deque([_norm(skill)])

        while queue:
            curr = queue.popleft()
            for p in self._prereqs.get(curr, ()):
                if p not in visited:
                    visited.add(p)
                    queue.append(p)

        return visited

    def has_prerequisite(self, skill: str, target_prereq: str) -> bool:
        """Check if target_prereq is a direct or transitive prerequisite of skill."""
        return _norm(target_prereq) in self.get_all_prerequisites(skill)

    def sort_skills(self, skills: list[str]) -> list[str]:
        """Sort a list of skills in topological learning order.

        Foundational prerequisites come before dependent technologies.
        Preserves deterministic ordering for skills with no mutual dependency.
        Handles cycles gracefully by falling back to natural order.

        Args:
            skills: List of skill names.

        Returns:
            Topologically sorted list of skills (preserving original capitalization).
        """
        if not skills:
            return []

        # Map normalized to original casing (first occurrence wins)
        display_map: dict[str, str] = {}
        for s in skills:
            k = _norm(s)
            if k not in display_map:
                display_map[k] = s

        skill_keys = set(display_map.keys())

        # Build in-degree and adjacency for the subgraph restricted to given skills
        in_degree: dict[str, int] = {k: 0 for k in skill_keys}
        dependents: dict[str, list[str]] = {k: [] for k in skill_keys}

        for k in skill_keys:
            for p in self._prereqs.get(k, ()):
                if p in skill_keys:
                    # p must be learned before k
                    dependents[p].append(k)
                    in_degree[k] += 1

        # Kahn's algorithm: queue nodes with in_degree == 0
        queue = deque(sorted([k for k, deg in in_degree.items() if deg == 0]))
        sorted_keys: list[str] = []

        while queue:
            curr = queue.popleft()
            sorted_keys.append(curr)

            for dep in dependents[curr]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        # In case of cycles or disconnected components not reached
        if len(sorted_keys) < len(skill_keys):
            unvisited = [k for k in skill_keys if k not in sorted_keys]
            sorted_keys.extend(sorted(unvisited))

        return [display_map[k] for k in sorted_keys]

    def group_into_dependency_levels(self, skills: list[str]) -> list[list[str]]:
        """Partition skills into progressive dependency tiers.

        - Level 0: Foundations with no prerequisites within the input set.
        - Level 1: Tools whose prerequisites are in Level 0.
        - Level 2+: Advanced skills building on previous levels.

        Args:
            skills: List of skill names.

        Returns:
            List of skill name lists, one per tier.
        """
        if not skills:
            return []

        display_map: dict[str, str] = {}
        for s in skills:
            k = _norm(s)
            if k not in display_map:
                display_map[k] = s

        remaining_keys = set(display_map.keys())
        satisfied_keys: set[str] = set()
        levels: list[list[str]] = []

        while remaining_keys:
            # Find all skills whose prerequisites (within the input set) are satisfied
            current_tier: list[str] = []
            for k in sorted(remaining_keys):
                prereqs = set(self._prereqs.get(k, ())) & set(display_map.keys())
                if prereqs.issubset(satisfied_keys):
                    current_tier.append(k)

            if not current_tier:
                # Cycle or mutual dependency detected: pop remaining to break stall
                current_tier = sorted(list(remaining_keys))

            levels.append([display_map[k] for k in current_tier])
            satisfied_keys.update(current_tier)
            remaining_keys -= set(current_tier)

        return levels


skill_prerequisite_graph = SkillPrerequisiteGraph()
