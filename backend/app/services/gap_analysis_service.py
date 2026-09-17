"""Database-backed Gap Analysis Service.

Connects the database entities (TargetRole, RoleSkillWeighting, User, UserSkill)
with the stateless SkillGapAnalyzer and SkillExtractor NLP engines.
"""

from __future__ import annotations

from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.job import JobPosting
from app.models.role import RoleSkillWeighting, TargetRole, UserTargetRole
from app.models.user import User
from app.services.skill_extractor import ExtractedSkill, skill_extractor
from app.services.skill_gap_analyzer import GapReport, SkillGapAnalyzer, SkillWeight, skill_gap_analyzer
from app.services.user_skill_service import user_skill_service


class GapAnalysisService:
    """Service layer connecting database models with skill gap analytics."""

    def __init__(self, analyzer: SkillGapAnalyzer | None = None) -> None:
        self.analyzer = analyzer or skill_gap_analyzer

    def find_target_role(
        self,
        db: Session,
        *,
        role_id: int | None = None,
        role_name: str | None = None,
        role_slug: str | None = None,
    ) -> TargetRole | None:
        """Locate a TargetRole entity by ID, slug, or title (case-insensitive)."""
        if role_id is not None:
            return db.get(TargetRole, role_id)

        if role_slug:
            stmt = select(TargetRole).where(TargetRole.slug == role_slug.strip().lower())
            role = db.scalar(stmt)
            if role:
                return role

        if role_name:
            clean = role_name.strip()
            stmt = select(TargetRole).where(func.lower(TargetRole.title) == clean.lower())
            role = db.scalar(stmt)
            if role:
                return role
            # Fallback to partial match
            stmt = select(TargetRole).where(TargetRole.title.ilike(f"%{clean}%"))
            return db.scalar(stmt)

        return None

    def get_role_skill_weights(self, db: Session, role: TargetRole) -> list[SkillWeight]:
        """Fetch benchmark skill weightings for a target role."""
        stmt = (
            select(RoleSkillWeighting)
            .where(RoleSkillWeighting.role_id == role.id)
            .options(joinedload(RoleSkillWeighting.skill))
        )
        weightings = list(db.scalars(stmt).all())
        return [
            SkillWeight(name=rw.skill.name, weight=rw.weight)
            for rw in weightings
            if rw.skill
        ]

    def analyse_skills(
        self,
        db: Session,
        *,
        profile_skills: list[str],
        role_id: int | None = None,
        role_name: str | None = None,
        role_slug: str | None = None,
    ) -> dict[str, Any]:
        """Compute a skill gap report for a given set of skills against a target role."""
        target_role = self.find_target_role(
            db, role_id=role_id, role_name=role_name, role_slug=role_slug
        )

        effective_role_name = (
            target_role.title if target_role else (role_name or role_slug or "Target Role")
        )
        required_weights: list[SkillWeight] = []

        if target_role:
            required_weights = self.get_role_skill_weights(db, target_role)

        report = self.analyzer.analyse(
            profile_skills=profile_skills,
            required_skills=required_weights,
            role_name=effective_role_name,
        )

        result = report.to_dict()
        result["role_id"] = target_role.id if target_role else None
        result["category"] = target_role.category if target_role else None
        result["min_experience_years"] = (
            target_role.min_experience_years if target_role else None
        )
        return result

    def analyse_from_text(
        self,
        db: Session,
        *,
        text: str,
        role_id: int | None = None,
        role_name: str | None = None,
        role_slug: str | None = None,
        min_confidence: float = 0.60,
    ) -> dict[str, Any]:
        """Extract skills from free-form text and compute gap against target role."""
        extracted: list[ExtractedSkill] = skill_extractor.extract_skills(
            text, min_confidence=min_confidence
        )
        extracted_names = [s.name for s in extracted]

        gap_report = self.analyse_skills(
            db,
            profile_skills=extracted_names,
            role_id=role_id,
            role_name=role_name,
            role_slug=role_slug,
        )

        return {
            "extracted_skills": [s.to_dict() for s in extracted],
            "gap_report": gap_report,
        }

    def analyse_for_user(
        self,
        db: Session,
        *,
        user_id: int,
        role_id: int | None = None,
        role_name: str | None = None,
        role_slug: str | None = None,
    ) -> dict[str, Any]:
        """Compute gap report for a registered user's profile and persist readiness score."""
        user = db.get(User, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        claimed_skills = user_skill_service.get_user_skill_names(db, user_id=user_id)

        report = self.analyse_skills(
            db,
            profile_skills=claimed_skills,
            role_id=role_id,
            role_name=role_name,
            role_slug=role_slug,
        )

        # Update readiness score on UserTargetRole if role was found
        found_role_id = report.get("role_id")
        if found_role_id:
            stmt = select(UserTargetRole).where(
                UserTargetRole.user_id == user_id,
                UserTargetRole.role_id == found_role_id,
            )
            user_target_role = db.scalar(stmt)
            if not user_target_role:
                user_target_role = UserTargetRole(
                    user_id=user_id,
                    role_id=found_role_id,
                    readiness_score=report["weighted_gap_score"],
                )
                db.add(user_target_role)
            else:
                user_target_role.readiness_score = report["weighted_gap_score"]
            db.commit()

        return report


gap_analysis_service = GapAnalysisService()
