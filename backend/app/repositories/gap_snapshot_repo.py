"""Repository for skill gap analysis snapshots."""

from __future__ import annotations

from typing import Any
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.gap_snapshot import SkillGapSnapshot
from app.repositories.base import BaseRepository


class SkillGapSnapshotRepository(BaseRepository[SkillGapSnapshot]):
    """Data access repository for candidate skill gap history."""

    def __init__(self) -> None:
        super().__init__(SkillGapSnapshot)

    def create_snapshot(
        self,
        db: Session,
        *,
        user_id: int,
        role_id: int | None,
        role_title: str,
        readiness_score: float,
        matched_skills: list[dict[str, Any]],
        missing_skills: list[dict[str, Any]],
    ) -> SkillGapSnapshot:
        """Record a new gap analysis calculation for historical tracking."""
        snapshot = SkillGapSnapshot(
            user_id=user_id,
            role_id=role_id,
            role_title=role_title,
            readiness_score=readiness_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    def list_snapshots(
        self,
        db: Session,
        *,
        user_id: int,
        limit: int = 20,
    ) -> list[SkillGapSnapshot]:
        """Fetch candidate's historical gap evaluations, latest first."""
        stmt = (
            select(SkillGapSnapshot)
            .where(SkillGapSnapshot.user_id == user_id)
            .order_by(SkillGapSnapshot.created_at.desc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_latest_snapshot(
        self,
        db: Session,
        *,
        user_id: int,
        role_id: int | None = None,
    ) -> SkillGapSnapshot | None:
        """Fetch candidate's most recent snapshot, optionally filtered by role."""
        stmt = select(SkillGapSnapshot).where(SkillGapSnapshot.user_id == user_id)
        if role_id is not None:
            stmt = stmt.where(SkillGapSnapshot.role_id == role_id)
        stmt = stmt.order_by(SkillGapSnapshot.created_at.desc()).limit(1)
        return db.scalar(stmt)

    def delete_snapshot(
        self,
        db: Session,
        *,
        snapshot_id: int,
        user_id: int,
    ) -> bool:
        """Remove a snapshot belonging to the user."""
        stmt = delete(SkillGapSnapshot).where(
            SkillGapSnapshot.id == snapshot_id,
            SkillGapSnapshot.user_id == user_id,
        )
        res = db.execute(stmt)
        db.commit()
        return bool(res.rowcount and res.rowcount > 0)

    def get_user_snapshot_stats(
        self,
        db: Session,
        *,
        user_id: int,
    ) -> dict[str, Any]:
        """Aggregate snapshot metrics: total snapshots, avg readiness score, best score, trend."""
        stmt = (
            select(SkillGapSnapshot)
            .where(SkillGapSnapshot.user_id == user_id)
            .order_by(SkillGapSnapshot.created_at.asc())
        )
        snapshots = list(db.scalars(stmt).all())
        if not snapshots:
            return {
                "total_snapshots": 0,
                "average_readiness_score": 0.0,
                "highest_readiness_score": 0.0,
                "lowest_readiness_score": 0.0,
                "latest_readiness_score": 0.0,
                "score_trend": "neutral",
            }
        scores = [s.readiness_score for s in snapshots]
        avg_score = round(sum(scores) / len(scores), 2)
        highest = max(scores)
        lowest = min(scores)
        latest = scores[-1]
        first = scores[0]
        if len(scores) > 1:
            if latest > first:
                trend = "improving"
            elif latest < first:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "total_snapshots": len(snapshots),
            "average_readiness_score": avg_score,
            "highest_readiness_score": highest,
            "lowest_readiness_score": lowest,
            "latest_readiness_score": latest,
            "score_trend": trend,
        }


gap_snapshot_repository = SkillGapSnapshotRepository()
