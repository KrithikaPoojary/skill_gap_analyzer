"""Career role recommendation service.

Ranks target career roles against a candidate's skill set to deliver personalized,
weighted role recommendations and identify high-impact upskilling opportunities.
"""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.role import RoleSkillWeighting, TargetRole
from app.models.user import User
from app.services.skill_extractor import ExtractedSkill, skill_extractor
from app.services.skill_gap_analyzer import GapReport, SkillGapAnalyzer, SkillWeight, skill_gap_analyzer
from app.services.user_skill_service import user_skill_service


class RecommendationService:
    """Service layer for computing ranked career role recommendations."""

    def __init__(self, analyzer: SkillGapAnalyzer | None = None) -> None:
        self.analyzer = analyzer or skill_gap_analyzer

    def _get_active_roles(
        self,
        db: Session,
        *,
        category: str | None = None,
    ) -> list[TargetRole]:
        """Fetch all active target roles with role_skills and skills eagerly loaded."""
        stmt = (
            select(TargetRole)
            .where(TargetRole.is_active.is_(True))
            .options(
                joinedload(TargetRole.role_skills).joinedload(RoleSkillWeighting.skill)
            )
        )
        if category:
            stmt = stmt.where(TargetRole.category == category)
        return list(db.scalars(stmt).unique().all())

    def recommend_for_skills(
        self,
        db: Session,
        *,
        skills: list[str],
        limit: int = 5,
        min_score: float = 0.0,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Rank target roles by fit score for a given list of skills.

        Args:
            db: Database session.
            skills: List of candidate skills.
            limit: Maximum recommendations to return.
            min_score: Minimum match score threshold [0.0, 1.0].
            category: Optional category filter.

        Returns:
            List of ranked recommendation dicts.
        """
        roles = self._get_active_roles(db, category=category)
        if not roles:
            return []

        recommendations: list[dict[str, Any]] = []

        for role in roles:
            required_weights = [
                SkillWeight(name=rw.skill.name, weight=rw.weight)
                for rw in role.role_skills
                if rw.skill
            ]

            report: GapReport = self.analyzer.analyse(
                profile_skills=skills,
                required_skills=required_weights,
                role_name=role.title,
            )

            if report.weighted_gap_score >= min_score:
                recommendations.append(
                    {
                        "role_id": role.id,
                        "title": role.title,
                        "slug": role.slug,
                        "category": role.category,
                        "min_experience_years": role.min_experience_years,
                        "match_score": report.weighted_gap_score,
                        "coverage_pct": report.coverage_pct,
                        "matched_skills": report.matched_skills,
                        "missing_skills": [
                            {"name": sw.name, "weight": round(sw.weight, 3)}
                            for sw in report.missing_skills
                        ],
                        "missing_critical": report.missing_critical,
                    }
                )

        # Sort descending by match score, secondary by coverage percentage
        recommendations.sort(
            key=lambda r: (r["match_score"], r["coverage_pct"]),
            reverse=True,
        )

        return recommendations[:limit]

    def recommend_for_user(
        self,
        db: Session,
        *,
        user_id: int,
        limit: int = 5,
        min_score: float = 0.0,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate role recommendations for a registered user based on their claimed skills."""
        user = db.get(User, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        claimed_skills = user_skill_service.get_user_skill_names(db, user_id=user_id)
        return self.recommend_for_skills(
            db,
            skills=claimed_skills,
            limit=limit,
            min_score=min_score,
            category=category,
        )

    def recommend_for_text(
        self,
        db: Session,
        *,
        text: str,
        limit: int = 5,
        min_score: float = 0.0,
        category: str | None = None,
        min_confidence: float = 0.60,
    ) -> dict[str, Any]:
        """Extract skills from free-form text and deliver role recommendations."""
        extracted: list[ExtractedSkill] = skill_extractor.extract_skills(
            text, min_confidence=min_confidence
        )
        extracted_names = [s.name for s in extracted]

        recommendations = self.recommend_for_skills(
            db,
            skills=extracted_names,
            limit=limit,
            min_score=min_score,
            category=category,
        )

        return {
            "extracted_skills": [s.to_dict() for s in extracted],
            "recommendations": recommendations,
        }


recommendation_service = RecommendationService()
