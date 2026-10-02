"""Platform statistics service for admin dashboards and monitoring."""

from __future__ import annotations

from typing import Any
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.associations import UserSkill
from app.models.gap_snapshot import SkillGapSnapshot
from app.models.job import JobPosting
from app.models.notification import Notification
from app.models.role import TargetRole, UserTargetRole
from app.models.user import Profile, User


class PlatformStatsService:
    """Aggregate platform-wide statistics for admin and health dashboards."""

    def get_user_stats(self, db: Session) -> dict[str, Any]:
        """Count total, active, inactive, and superuser accounts."""
        total = db.scalar(select(func.count()).select_from(User)) or 0
        active = db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0
        superusers = db.scalar(select(func.count()).select_from(User).where(User.is_superuser.is_(True))) or 0
        return {
            "total_users": total,
            "active_users": active,
            "inactive_users": total - active,
            "superuser_count": superusers,
        }

    def get_job_stats(self, db: Session) -> dict[str, Any]:
        """Count total job postings and active listings."""
        total = db.scalar(select(func.count()).select_from(JobPosting)) or 0
        active = db.scalar(
            select(func.count()).select_from(JobPosting).where(JobPosting.is_active.is_(True))
        ) or 0
        return {
            "total_jobs": total,
            "active_jobs": active,
            "inactive_jobs": total - active,
        }

    def get_skill_stats(self, db: Session) -> dict[str, Any]:
        """Count user skill associations and average skills per user."""
        total_associations = db.scalar(select(func.count()).select_from(UserSkill)) or 0
        total_users_with_skills = db.scalar(
            select(func.count(func.distinct(UserSkill.user_id))).select_from(UserSkill)
        ) or 0
        avg_skills = round(total_associations / total_users_with_skills, 2) if total_users_with_skills > 0 else 0.0
        return {
            "total_user_skill_associations": total_associations,
            "users_with_skills": total_users_with_skills,
            "avg_skills_per_user": avg_skills,
        }

    def get_role_stats(self, db: Session) -> dict[str, Any]:
        """Count target roles and user career tracking associations."""
        total_roles = db.scalar(select(func.count()).select_from(TargetRole)) or 0
        active_roles = db.scalar(
            select(func.count()).select_from(TargetRole).where(TargetRole.is_active.is_(True))
        ) or 0
        tracked_assocs = db.scalar(select(func.count()).select_from(UserTargetRole)) or 0
        return {
            "total_target_roles": total_roles,
            "active_target_roles": active_roles,
            "user_target_role_associations": tracked_assocs,
        }

    def get_gap_analysis_stats(self, db: Session) -> dict[str, Any]:
        """Aggregate gap analysis snapshot statistics."""
        total_snapshots = db.scalar(select(func.count()).select_from(SkillGapSnapshot)) or 0
        avg_readiness = db.scalar(select(func.avg(SkillGapSnapshot.readiness_score))) or 0.0
        return {
            "total_gap_snapshots": total_snapshots,
            "avg_platform_readiness_score": round(float(avg_readiness), 2),
        }

    def get_notification_stats(self, db: Session) -> dict[str, Any]:
        """Count total and unread notifications platform-wide."""
        total = db.scalar(select(func.count()).select_from(Notification)) or 0
        unread = db.scalar(
            select(func.count()).select_from(Notification).where(Notification.is_read.is_(False))
        ) or 0
        return {
            "total_notifications": total,
            "unread_notifications": unread,
        }

    def get_overview(self, db: Session) -> dict[str, Any]:
        """Full platform dashboard summary."""
        return {
            "users": self.get_user_stats(db),
            "jobs": self.get_job_stats(db),
            "skills": self.get_skill_stats(db),
            "roles": self.get_role_stats(db),
            "gap_analysis": self.get_gap_analysis_stats(db),
            "notifications": self.get_notification_stats(db),
        }


platform_stats_service = PlatformStatsService()
