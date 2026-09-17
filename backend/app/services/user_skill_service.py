"""User skill management service.

Handles adding, updating, removing, and querying technical skills linked to
user profiles via the UserSkill association entity.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.associations import UserSkill
from app.models.skill import Skill
from app.models.user import User
from app.repositories.skill_repo import skill_repository


class UserSkillService:
    """Service layer for user profile skill operations."""

    def add_user_skill(
        self,
        db: Session,
        *,
        user_id: int,
        skill_id: int | None = None,
        skill_name: str | None = None,
        proficiency_level: str = "intermediate",
        years_of_experience: float = 1.0,
        is_verified: bool = False,
    ) -> UserSkill:
        """Add or update a skill on a user's profile.

        Args:
            db: Database session.
            user_id: Target user ID.
            skill_id: Optional ID of an existing skill.
            skill_name: Optional name of the skill. If not found in taxonomy,
                a new unverified skill record is automatically created.
            proficiency_level: beginner, intermediate, advanced, expert.
            years_of_experience: Years practicing this skill.
            is_verified: Whether the skill was verified.

        Returns:
            The created or updated UserSkill instance.

        Raises:
            ValueError: If user doesn't exist or neither skill_id nor skill_name is given.
        """
        user = db.get(User, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        skill: Skill | None = None
        if skill_id is not None:
            skill = db.get(Skill, skill_id)
            if not skill:
                raise ValueError(f"Skill with ID {skill_id} not found.")
        elif skill_name:
            clean_name = skill_name.strip()
            norm = Skill.normalize(clean_name)
            skill = skill_repository.get_by_normalized_name(db, normalized_name=norm)
            if not skill:
                skill = skill_repository.get_by_name(db, name=clean_name)
            if not skill:
                # Auto-create taxonomy entry for ad-hoc candidate skills
                skill = Skill(
                    name=clean_name,
                    normalized_name=norm,
                    category="other",
                    is_verified=False,
                )
                db.add(skill)
                db.flush()
        else:
            raise ValueError("Either skill_id or skill_name must be provided.")

        stmt = select(UserSkill).where(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill.id,
        )
        user_skill = db.scalar(stmt)
        if user_skill:
            user_skill.proficiency_level = proficiency_level
            user_skill.years_of_experience = years_of_experience
            user_skill.is_verified = is_verified
        else:
            user_skill = UserSkill(
                user_id=user_id,
                skill_id=skill.id,
                proficiency_level=proficiency_level,
                years_of_experience=years_of_experience,
                is_verified=is_verified,
            )
            db.add(user_skill)

        db.commit()
        db.refresh(user_skill)
        return user_skill

    def remove_user_skill(self, db: Session, *, user_id: int, skill_id: int) -> bool:
        """Remove a skill association from a user.

        Returns:
            True if removed, False if not found.
        """
        stmt = select(UserSkill).where(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id,
        )
        user_skill = db.scalar(stmt)
        if not user_skill:
            return False

        db.delete(user_skill)
        db.commit()
        return True

    def get_user_skills(self, db: Session, *, user_id: int) -> list[UserSkill]:
        """Fetch all skills associated with a user, with Skill entity eagerly loaded."""
        stmt = (
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .options(joinedload(UserSkill.skill))
        )
        return list(db.scalars(stmt).all())

    def get_user_skill_names(self, db: Session, *, user_id: int) -> list[str]:
        """Fetch canonical names of all skills claimed by a user."""
        skills = self.get_user_skills(db, user_id=user_id)
        return [us.skill.name for us in skills if us.skill]

    def bulk_add_user_skills(
        self,
        db: Session,
        *,
        user_id: int,
        skill_names: list[str],
        proficiency_level: str = "intermediate",
    ) -> list[UserSkill]:
        """Convenience method to associate multiple skills with a user."""
        results = []
        for name in skill_names:
            if not name or not name.strip():
                continue
            item = self.add_user_skill(
                db,
                user_id=user_id,
                skill_name=name.strip(),
                proficiency_level=proficiency_level,
            )
            results.append(item)
        return results


user_skill_service = UserSkillService()
