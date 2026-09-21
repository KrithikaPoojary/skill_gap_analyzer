"""User profile management service.

Handles fetching, creating, and updating user professional profiles
and aggregating profile data with claimed skills and target career roles.
"""

from __future__ import annotations

from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.associations import UserSkill
from app.models.role import UserTargetRole
from app.models.user import Profile, User


class ProfileService:
    """Service layer for Profile CRUD and aggregation operations."""

    def get_by_user_id(self, db: Session, user_id: int) -> Profile | None:
        """Fetch profile for a specific user ID."""
        stmt = select(Profile).where(Profile.user_id == user_id)
        return db.scalar(stmt)

    def upsert_profile(
        self,
        db: Session,
        *,
        user_id: int,
        headline: str | None = None,
        bio: str | None = None,
        current_title: str | None = None,
        years_of_experience: float | None = None,
        location: str | None = None,
        resume_url: str | None = None,
        github_url: str | None = None,
        linkedin_url: str | None = None,
    ) -> Profile:
        """Create or update a user's professional profile.

        Args:
            db: Database session.
            user_id: User ID.
            headline: Professional headline.
            bio: Short biography or summary.
            current_title: Current job title.
            years_of_experience: Total professional experience.
            location: Geographical location.
            resume_url: Link to resume or uploaded file.
            github_url: GitHub profile URL.
            linkedin_url: LinkedIn profile URL.

        Returns:
            The created or updated Profile instance.

        Raises:
            ValueError: If user does not exist.
        """
        user = db.get(User, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        profile = self.get_by_user_id(db, user_id)
        if not profile:
            profile = Profile(
                user_id=user_id,
                headline=headline,
                bio=bio,
                current_title=current_title,
                years_of_experience=years_of_experience if years_of_experience is not None else 0.0,
                location=location,
                resume_url=resume_url,
                github_url=github_url,
                linkedin_url=linkedin_url,
            )
            db.add(profile)
        else:
            if headline is not None:
                profile.headline = headline
            if bio is not None:
                profile.bio = bio
            if current_title is not None:
                profile.current_title = current_title
            if years_of_experience is not None:
                profile.years_of_experience = years_of_experience
            if location is not None:
                profile.location = location
            if resume_url is not None:
                profile.resume_url = resume_url
            if github_url is not None:
                profile.github_url = github_url
            if linkedin_url is not None:
                profile.linkedin_url = linkedin_url

        db.commit()
        db.refresh(profile)
        return profile

    def get_full_profile(self, db: Session, user_id: int) -> dict[str, Any] | None:
        """Fetch user profile with associated skills and target roles eager loaded.

        Returns:
            Aggregated dictionary representation or None if user not found.
        """
        user = db.get(User, user_id)
        if not user:
            return None

        profile = self.get_by_user_id(db, user_id)

        # Eager load user skills with skill details
        skill_stmt = (
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .options(joinedload(UserSkill.skill))
        )
        user_skills = list(db.scalars(skill_stmt).all())

        # Eager load target roles
        role_stmt = (
            select(UserTargetRole)
            .where(UserTargetRole.user_id == user_id)
            .options(joinedload(UserTargetRole.role))
        )
        target_roles = list(db.scalars(role_stmt).all())

        return {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "profile": {
                "headline": profile.headline if profile else None,
                "bio": profile.bio if profile else None,
                "current_title": profile.current_title if profile else None,
                "years_of_experience": profile.years_of_experience if profile else 0.0,
                "location": profile.location if profile else None,
                "resume_url": profile.resume_url if profile else None,
                "github_url": profile.github_url if profile else None,
                "linkedin_url": profile.linkedin_url if profile else None,
            },
            "skills": [
                {
                    "skill_id": us.skill_id,
                    "name": us.skill.name if us.skill else None,
                    "normalized_name": us.skill.normalized_name if us.skill else None,
                    "category": us.skill.category if us.skill else None,
                    "proficiency_level": us.proficiency_level,
                    "years_of_experience": us.years_of_experience,
                    "is_verified": us.is_verified,
                }
                for us in user_skills
            ],
            "target_roles": [
                {
                    "role_id": utr.role_id,
                    "title": utr.role.title if utr.role else None,
                    "slug": utr.role.slug if utr.role else None,
                    "readiness_score": utr.readiness_score,
                    "target_date": utr.target_date.isoformat() if utr.target_date else None,
                }
                for utr in target_roles
            ],
        }

    def get_user_stats(self, db: Session, user_id: int) -> dict[str, Any]:
        """Return aggregated profile statistics for a user."""
        from app.models.roadmap import LearningRoadmap

        profile = self.get_by_user_id(db, user_id=user_id)
        skills_stmt = select(UserSkill).where(UserSkill.user_id == user_id)
        user_skills = list(db.scalars(skills_stmt).all())

        roadmap_count = db.scalar(
            select(LearningRoadmap).where(LearningRoadmap.user_id == user_id)
        )

        proficiency_map = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
        levels = [proficiency_map.get(s.proficiency_level or "", 0) for s in user_skills]
        avg_proficiency = round(sum(levels) / len(levels), 2) if levels else 0.0

        return {
            "total_skills": len(user_skills),
            "avg_proficiency_score": avg_proficiency,
            "headline": profile.headline if profile else None,
            "years_of_experience": profile.years_of_experience if profile else None,
            "profile_complete": profile is not None,
        }


profile_service = ProfileService()
