"""Database-backed Roadmap Application Service.

Coordinates domain roadmap generation with gap analysis, user profile data,
and database persistence.
"""

from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from app.models.roadmap import LearningRoadmap, RoadmapMilestone
from app.models.user import User
from app.repositories.roadmap_repo import RoadmapRepository, roadmap_repository
from app.services.gap_analysis_service import GapAnalysisService, gap_analysis_service
from app.services.roadmap.resource_catalog import learning_resource_catalog
from app.services.roadmap.roadmap_generator import (
    GeneratedRoadmap,
    RoadmapGenerator,
    roadmap_generator,
)


class RoadmapService:
    """Application service for roadmap generation, persistence, and milestone tracking."""

    def __init__(
        self,
        generator: RoadmapGenerator | None = None,
        gap_service: GapAnalysisService | None = None,
        repo: RoadmapRepository | None = None,
    ) -> None:
        self.generator = generator or roadmap_generator
        self.gap_service = gap_service or gap_analysis_service
        self.repo = repo or roadmap_repository

    def generate_transient(
        self,
        *,
        missing_skills: list[str],
        role_title: str = "Target Role",
        weekly_commitment_hours: int = 10,
    ) -> dict[str, Any]:
        """Generate in-memory roadmap without database persistence."""
        roadmap: GeneratedRoadmap = self.generator.generate(
            missing_skills=missing_skills,
            role_title=role_title,
            weekly_commitment_hours=weekly_commitment_hours,
        )
        return roadmap.to_dict()

    def generate_from_text(
        self,
        db: Session,
        *,
        text: str,
        role_id: int | None = None,
        role_name: str | None = None,
        role_slug: str | None = None,
        weekly_commitment_hours: int = 10,
        min_confidence: float = 0.60,
    ) -> dict[str, Any]:
        """Extract skills from text, compute gap against target role, and sequence roadmap."""
        analysis = self.gap_service.analyse_from_text(
            db,
            text=text,
            role_id=role_id,
            role_name=role_name,
            role_slug=role_slug,
            min_confidence=min_confidence,
        )
        gap_report = analysis["gap_report"]
        missing_names = [s["name"] for s in gap_report.get("missing_skills", [])]
        effective_role = gap_report.get("role_name", "Target Role")

        roadmap = self.generator.generate(
            missing_skills=missing_names,
            role_title=effective_role,
            weekly_commitment_hours=weekly_commitment_hours,
        )

        return {
            "extracted_skills": analysis["extracted_skills"],
            "gap_report": gap_report,
            "roadmap": roadmap.to_dict(),
        }

    def create_and_persist_for_user(
        self,
        db: Session,
        *,
        user_id: int,
        role_id: int | None = None,
        role_name: str | None = None,
        role_slug: str | None = None,
        weekly_commitment_hours: int = 10,
    ) -> dict[str, Any]:
        """Compute gap report for user, generate roadmap, and save to database."""
        user = db.get(User, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        gap_report = self.gap_service.analyse_for_user(
            db,
            user_id=user_id,
            role_id=role_id,
            role_name=role_name,
            role_slug=role_slug,
        )

        missing_names = [s["name"] for s in gap_report.get("missing_skills", [])]
        effective_role = gap_report.get("role_name", "Target Role")
        target_role_id = gap_report.get("role_id")

        roadmap_data: GeneratedRoadmap = self.generator.generate(
            missing_skills=missing_names,
            role_title=effective_role,
            weekly_commitment_hours=weekly_commitment_hours,
        )

        # Convert GeneratedRoadmap phases to dict format expected by repo
        phases_payload = [p.to_dict() for p in roadmap_data.phases]

        saved_roadmap: LearningRoadmap = self.repo.create_roadmap_with_phases(
            db,
            user_id=user_id,
            target_role_id=target_role_id,
            title=f"{effective_role} Learning Path",
            target_role_name=effective_role,
            total_skills=roadmap_data.total_skills,
            total_estimated_hours=roadmap_data.total_estimated_hours,
            weekly_commitment_hours=roadmap_data.weekly_commitment_hours,
            estimated_weeks=roadmap_data.estimated_weeks,
            phases_data=phases_payload,
        )

        return self._format_roadmap_model(saved_roadmap)

    def get_user_roadmaps(
        self,
        db: Session,
        *,
        user_id: int,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all roadmaps created for a user."""
        roadmaps = self.repo.get_user_roadmaps(db, user_id=user_id, status=status)
        return [self._format_roadmap_model(rm) for rm in roadmaps]

    def get_roadmap_by_id(self, db: Session, *, roadmap_id: int) -> dict[str, Any] | None:
        """Fetch complete roadmap with milestones by ID."""
        rm = self.repo.get_by_id_with_milestones(db, roadmap_id=roadmap_id)
        if not rm:
            return None
        return self._format_roadmap_model(rm)

    def get_user_roadmap_by_id(self, db: Session, *, user_id: int, roadmap_id: int) -> dict[str, Any] | None:
        """Fetch complete roadmap with milestones by ID ensuring user ownership."""
        rm = self.repo.get_by_id_with_milestones(db, roadmap_id=roadmap_id)
        if not rm or rm.user_id != user_id:
            return None
        return self._format_roadmap_model(rm)


    def update_milestone_progress(
        self,
        db: Session,
        *,
        milestone_id: int,
        is_completed: bool,
    ) -> dict[str, Any] | None:
        """Update completion status of a milestone."""
        milestone = self.repo.update_milestone_completion(
            db, milestone_id=milestone_id, is_completed=is_completed
        )
        if not milestone:
            return None
        return {
            "id": milestone.id,
            "roadmap_id": milestone.roadmap_id,
            "phase_number": milestone.phase_number,
            "phase_title": milestone.phase_title,
            "is_completed": milestone.is_completed,
        }

    def update_user_milestone_progress(
        self,
        db: Session,
        *,
        user_id: int,
        roadmap_id: int,
        milestone_id: int,
        is_completed: bool,
    ) -> dict[str, Any] | None:
        """Update completion status of a milestone ensuring roadmap ownership."""
        roadmap = self.repo.get_by_id_with_milestones(db, roadmap_id=roadmap_id)
        if not roadmap or roadmap.user_id != user_id:
            return None

        # Verify milestone belongs to this roadmap
        milestone = next((m for m in roadmap.milestones if m.id == milestone_id), None)
        if not milestone:
            return None

        updated = self.repo.update_milestone_completion(
            db, milestone_id=milestone_id, is_completed=is_completed
        )
        if not updated:
            return None

        # Calculate progress
        total_milestones = len(roadmap.milestones)
        completed_count = sum(
            1 for m in roadmap.milestones
            if (m.id == milestone_id and is_completed) or (m.id != milestone_id and m.is_completed)
        )
        progress_pct = round((completed_count / total_milestones) * 100.0, 1) if total_milestones > 0 else 0.0

        return {
            "milestone_id": updated.id,
            "roadmap_id": roadmap.id,
            "phase_number": updated.phase_number,
            "phase_title": updated.phase_title,
            "is_completed": updated.is_completed,
            "roadmap_milestones_completed": completed_count,
            "roadmap_milestones_total": total_milestones,
            "roadmap_progress_percentage": progress_pct,
        }

    def delete_user_roadmap(self, db: Session, *, user_id: int, roadmap_id: int) -> bool:
        """Delete roadmap belonging to user."""
        return self.repo.delete_user_roadmap(db, roadmap_id=roadmap_id, user_id=user_id)

    def update_user_roadmap_status(
        self, db: Session, *, user_id: int, roadmap_id: int, status: str
    ) -> dict[str, Any] | None:
        """Update roadmap status (e.g. active, completed, archived)."""
        rm = self.repo.update_roadmap_status(db, roadmap_id=roadmap_id, user_id=user_id, status=status)
        if not rm:
            return None
        return self._format_roadmap_model(rm)

    def get_user_progress_summary(self, db: Session, *, user_id: int) -> dict[str, Any]:
        """Aggregate progress across all roadmaps belonging to user."""
        roadmaps = self.repo.get_user_roadmaps(db, user_id=user_id)
        total_roadmaps = len(roadmaps)
        active_roadmaps = sum(1 for r in roadmaps if r.status == "active")
        completed_roadmaps = sum(1 for r in roadmaps if r.status == "completed")

        total_milestones = sum(len(r.milestones) for r in roadmaps)
        completed_milestones = sum(
            1 for r in roadmaps for m in r.milestones if m.is_completed
        )

        total_skills = sum(
            len(m.skills) for r in roadmaps for m in r.milestones
        )
        completed_skills = sum(
            1 for r in roadmaps for m in r.milestones for s in m.skills if s.is_completed
        )

        completion_pct = (
            round((completed_skills / total_skills) * 100.0, 1)
            if total_skills > 0
            else 0.0
        )

        return {
            "total_roadmaps": total_roadmaps,
            "active_roadmaps": active_roadmaps,
            "completed_roadmaps": completed_roadmaps,
            "total_milestones": total_milestones,
            "completed_milestones": completed_milestones,
            "total_skills": total_skills,
            "completed_skills": completed_skills,
            "overall_completion_percentage": completion_pct,
        }


    def _format_roadmap_model(self, rm: LearningRoadmap) -> dict[str, Any]:
        """Transform SQLAlchemy ORM model to dictionary with embedded resources."""
        milestones_list = []
        for m in sorted(rm.milestones, key=lambda x: x.order_index):
            skills_list = []
            for s in m.skills:
                meta = learning_resource_catalog.get_skill_metadata(s.skill_name)
                skills_list.append(
                    {
                        "name": s.skill_name,
                        "category": meta.category,
                        "difficulty": s.difficulty,
                        "estimated_hours": s.estimated_hours,
                        "recommended_practice": meta.recommended_practice,
                        "is_completed": s.is_completed,
                        "resources": [r.to_dict() for r in meta.resources],
                    }
                )

            milestones_list.append(
                {
                    "id": m.id,
                    "phase_number": m.phase_number,
                    "phase_title": m.phase_title,
                    "description": m.description,
                    "total_phase_hours": m.total_phase_hours,
                    "estimated_weeks": m.estimated_weeks,
                    "capstone_project_title": m.capstone_project_title,
                    "capstone_project_description": m.capstone_project_description,
                    "is_completed": m.is_completed,
                    "skills": skills_list,
                }
            )

        return {
            "id": rm.id,
            "user_id": rm.user_id,
            "target_role_id": rm.target_role_id,
            "title": rm.title,
            "target_role_name": rm.target_role_name,
            "total_skills": rm.total_skills,
            "total_estimated_hours": rm.total_estimated_hours,
            "weekly_commitment_hours": rm.weekly_commitment_hours,
            "estimated_weeks": rm.estimated_weeks,
            "status": rm.status,
            "milestones": milestones_list,
        }


roadmap_service = RoadmapService()
