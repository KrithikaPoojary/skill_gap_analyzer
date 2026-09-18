"""Personalized Learning Roadmap Generator.

Sequences missing skills from a candidate's gap analysis into an actionable,
multi-phase curriculum with milestone project concepts, curated resources,
and realistic weekly pacing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from app.services.roadmap.prerequisite_graph import (
    SkillPrerequisiteGraph,
    skill_prerequisite_graph,
)
from app.services.roadmap.resource_catalog import (
    LearningResourceCatalog,
    SkillLearningMetadata,
    learning_resource_catalog,
)


@dataclass
class MilestoneSkillItem:
    """A skill item within a learning milestone."""

    name: str
    category: str
    difficulty: str
    estimated_hours: int
    recommended_practice: str
    resources: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "difficulty": self.difficulty,
            "estimated_hours": self.estimated_hours,
            "recommended_practice": self.recommended_practice,
            "resources": self.resources,
        }


@dataclass
class RoadmapMilestonePhase:
    """A progressive stage in the learning roadmap."""

    phase_number: int
    phase_title: str
    description: str
    skills: list[MilestoneSkillItem] = field(default_factory=list)
    total_phase_hours: int = 0
    estimated_weeks: int = 1
    capstone_project_title: str = ""
    capstone_project_description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_number": self.phase_number,
            "phase_title": self.phase_title,
            "description": self.description,
            "skills": [s.to_dict() for s in self.skills],
            "total_phase_hours": self.total_phase_hours,
            "estimated_weeks": self.estimated_weeks,
            "capstone_project_title": self.capstone_project_title,
            "capstone_project_description": self.capstone_project_description,
        }


@dataclass
class GeneratedRoadmap:
    """Complete personalized learning roadmap for a target role."""

    role_title: str
    total_skills: int
    total_estimated_hours: int
    weekly_commitment_hours: int
    estimated_weeks: int
    phases: list[RoadmapMilestonePhase] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_title": self.role_title,
            "total_skills": self.total_skills,
            "total_estimated_hours": self.total_estimated_hours,
            "weekly_commitment_hours": self.weekly_commitment_hours,
            "estimated_weeks": self.estimated_weeks,
            "phases": [p.to_dict() for p in self.phases],
        }


# Dynamic capstone project prompt generators based on phase number and skills
def _generate_capstone_project(
    phase_number: int,
    skills: list[str],
    role_title: str,
) -> tuple[str, str]:
    skill_names = ", ".join(skills[:3]) if skills else "the core curriculum"
    if phase_number == 1:
        return (
            f"Core Foundations: {role_title} Starter Project",
            f"Build a clean, well-tested prototype demonstrating fundamental proficiency in {skill_names}.",
        )
    elif phase_number == 2:
        return (
            f"Applied Tooling & Architecture Challenge",
            f"Develop and integrate modular services using {skill_names} following production design patterns.",
        )
    else:
        return (
            f"Production-Grade Capstone Deployment",
            f"Deploy an end-to-end scalable application utilizing {skill_names} with observability, automated CI/CD, and monitoring.",
        )


class RoadmapGenerator:
    """Orchestrates DAG dependency sequencing and curriculum construction."""

    def __init__(
        self,
        graph: SkillPrerequisiteGraph | None = None,
        catalog: LearningResourceCatalog | None = None,
    ) -> None:
        self.graph = graph or skill_prerequisite_graph
        self.catalog = catalog or learning_resource_catalog

    def generate(
        self,
        *,
        missing_skills: list[str],
        role_title: str = "Target Role",
        weekly_commitment_hours: int = 10,
    ) -> GeneratedRoadmap:
        """Generate a structured, progressive learning roadmap.

        Args:
            missing_skills: List of technical competencies the candidate lacks.
            role_title: Name of the aspirational career role.
            weekly_commitment_hours: Weekly study availability (e.g. 10 hrs/week).

        Returns:
            GeneratedRoadmap with progressive milestone phases and capstone projects.
        """
        # Clean & deduplicate
        clean_skills: list[str] = []
        seen = set()
        for s in missing_skills:
            norm = s.strip().lower()
            if norm and norm not in seen:
                seen.add(norm)
                clean_skills.append(s.strip())

        if not clean_skills:
            return GeneratedRoadmap(
                role_title=role_title,
                total_skills=0,
                total_estimated_hours=0,
                weekly_commitment_hours=weekly_commitment_hours,
                estimated_weeks=0,
                phases=[],
            )

        # Enforce positive weekly commitment
        pace = max(1, weekly_commitment_hours)

        # 1. Decompose into dependency tiers
        raw_tiers = self.graph.group_into_dependency_levels(clean_skills)

        # 2. Consolidate into 2 to 4 balanced milestone phases
        # If tiers > 3, combine adjacent tiers to maintain manageable milestones
        target_phases: list[list[str]] = []
        if len(raw_tiers) <= 3:
            target_phases = raw_tiers
        else:
            # First tier -> Phase 1, Middle tiers -> Phase 2, Last tiers -> Phase 3
            p1 = raw_tiers[0]
            p2 = [s for tier in raw_tiers[1:-1] for s in tier]
            p3 = raw_tiers[-1]
            target_phases = [p1, p2, p3]

        phase_titles = [
            ("Foundations & Core Prerequisites", "Establish core competencies and solve immediate blockers."),
            ("Applied Tooling & Frameworks", "Master modern application frameworks, databases, and development workflows."),
            ("Advanced Architecture & Production", "Solidify distributed systems, container orchestration, and cloud reliability."),
            ("Specialization & Domain Mastery", "Fine-tune edge competencies, testing frameworks, and advanced optimizations."),
        ]

        phases: list[RoadmapMilestonePhase] = []
        total_roadmap_hours = 0

        for i, skill_group in enumerate(target_phases):
            phase_num = i + 1
            title, desc = (
                phase_titles[i] if i < len(phase_titles) else (f"Advanced Milestone {phase_num}", "Advanced mastery.")
            )

            skill_items: list[MilestoneSkillItem] = []
            phase_hours = 0

            # Sort within the phase topologically
            sorted_phase_skills = self.graph.sort_skills(skill_group)

            for s_name in sorted_phase_skills:
                meta: SkillLearningMetadata = self.catalog.get_skill_metadata(s_name)
                phase_hours += meta.estimated_hours
                skill_items.append(
                    MilestoneSkillItem(
                        name=meta.skill_name,
                        category=meta.category,
                        difficulty=meta.difficulty,
                        estimated_hours=meta.estimated_hours,
                        recommended_practice=meta.recommended_practice,
                        resources=[r.to_dict() for r in meta.resources],
                    )
                )

            total_roadmap_hours += phase_hours
            phase_weeks = max(1, math.ceil(phase_hours / pace))
            proj_title, proj_desc = _generate_capstone_project(phase_num, sorted_phase_skills, role_title)

            phases.append(
                RoadmapMilestonePhase(
                    phase_number=phase_num,
                    phase_title=title,
                    description=desc,
                    skills=skill_items,
                    total_phase_hours=phase_hours,
                    estimated_weeks=phase_weeks,
                    capstone_project_title=proj_title,
                    capstone_project_description=proj_desc,
                )
            )

        total_weeks = max(1, math.ceil(total_roadmap_hours / pace))

        return GeneratedRoadmap(
            role_title=role_title,
            total_skills=len(clean_skills),
            total_estimated_hours=total_roadmap_hours,
            weekly_commitment_hours=pace,
            estimated_weeks=total_weeks,
            phases=phases,
        )


roadmap_generator = RoadmapGenerator()
