"""Learning Roadmap repository implementation."""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.roadmap import LearningRoadmap, MilestoneSkill, RoadmapMilestone
from app.repositories.base import BaseRepository


class RoadmapRepository(BaseRepository[LearningRoadmap]):
    """Data access repository for LearningRoadmap entities."""

    def __init__(self) -> None:
        super().__init__(LearningRoadmap)

    def get_by_id_with_milestones(self, db: Session, roadmap_id: int) -> LearningRoadmap | None:
        """Fetch a roadmap with all nested milestones and milestone skills eagerly loaded."""
        stmt = (
            select(LearningRoadmap)
            .where(LearningRoadmap.id == roadmap_id)
            .options(
                joinedload(LearningRoadmap.milestones).joinedload(RoadmapMilestone.skills)
            )
        )
        return db.scalar(stmt)

    def get_user_roadmaps(
        self,
        db: Session,
        *,
        user_id: int,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[LearningRoadmap]:
        """Fetch all roadmaps for a user, with optional status filter."""
        stmt = select(LearningRoadmap).where(LearningRoadmap.user_id == user_id)
        if status:
            stmt = stmt.where(LearningRoadmap.status == status)
        stmt = (
            stmt.options(
                joinedload(LearningRoadmap.milestones).joinedload(RoadmapMilestone.skills)
            )
            .order_by(LearningRoadmap.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).unique().all())

    def update_milestone_completion(
        self,
        db: Session,
        *,
        milestone_id: int,
        is_completed: bool,
    ) -> RoadmapMilestone | None:
        """Update completion status of a milestone and refresh roadmap status if all completed."""
        milestone = db.get(RoadmapMilestone, milestone_id)
        if not milestone:
            return None

        milestone.is_completed = is_completed
        # Also mark all skills in this milestone completed
        for ms in milestone.skills:
            ms.is_completed = is_completed

        db.flush()

        # Check if all milestones on parent roadmap are completed
        roadmap = db.get(LearningRoadmap, milestone.roadmap_id)
        if roadmap:
            all_done = all(m.is_completed for m in roadmap.milestones)
            if all_done and roadmap.milestones:
                roadmap.status = "completed"
            elif roadmap.status == "completed" and not all_done:
                roadmap.status = "active"

        db.commit()
        db.refresh(milestone)
        return milestone

    def create_roadmap_with_phases(
        self,
        db: Session,
        *,
        user_id: int | None,
        target_role_id: int | None,
        title: str,
        target_role_name: str,
        total_skills: int,
        total_estimated_hours: int,
        weekly_commitment_hours: int,
        estimated_weeks: int,
        phases_data: list[dict[str, Any]],
    ) -> LearningRoadmap:
        """Atomically persist a complete learning roadmap and all milestone phases."""
        roadmap = LearningRoadmap(
            user_id=user_id,
            target_role_id=target_role_id,
            title=title,
            target_role_name=target_role_name,
            total_skills=total_skills,
            total_estimated_hours=total_estimated_hours,
            weekly_commitment_hours=weekly_commitment_hours,
            estimated_weeks=estimated_weeks,
            status="active",
        )
        db.add(roadmap)
        db.flush()

        for p in phases_data:
            milestone = RoadmapMilestone(
                roadmap_id=roadmap.id,
                phase_number=p.get("phase_number", 1),
                phase_title=p.get("phase_title", "Phase"),
                description=p.get("description"),
                capstone_project_title=p.get("capstone_project_title"),
                capstone_project_description=p.get("capstone_project_description"),
                order_index=p.get("phase_number", 1) - 1,
                total_phase_hours=p.get("total_phase_hours", 0),
                estimated_weeks=p.get("estimated_weeks", 1),
                is_completed=False,
            )
            db.add(milestone)
            db.flush()

            for s in p.get("skills", []):
                ms = MilestoneSkill(
                    milestone_id=milestone.id,
                    skill_name=s.get("name") if isinstance(s, dict) else str(s),
                    estimated_hours=s.get("estimated_hours", 15) if isinstance(s, dict) else 15,
                    difficulty=s.get("difficulty", "intermediate") if isinstance(s, dict) else "intermediate",
                    is_completed=False,
                )
                db.add(ms)

        db.commit()
        db.refresh(roadmap)
        return roadmap


roadmap_repository = RoadmapRepository()
