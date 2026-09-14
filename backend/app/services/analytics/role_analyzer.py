"""Role frequency and market concentration analytics service.

Computes job market share by technical role, seniority breakdown per role archetype,
and remote availability metrics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.job import JobPosting
from app.schemas.enums import ExperienceLevel


@dataclass(frozen=True)
class RoleDistributionRecord:
    """Concentration and seniority metrics for a role track."""

    role_name: str
    total_postings: int
    market_share_pct: float
    seniority_breakdown: dict[str, int]
    remote_postings_count: int
    remote_pct: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RoleAnalyzer:
    """Analyzes role distribution and seniority concentration in job market data."""

    ROLE_TRACKS = [
        "Backend",
        "Frontend",
        "Full Stack",
        "DevOps",
        "Data Engineer",
        "Machine Learning",
        "QA Automation",
    ]

    def get_role_distributions(self, db: Session) -> list[RoleDistributionRecord]:
        """Compute distribution metrics grouped by core role tracks."""
        total_active_jobs = db.scalar(
            select(func.count(JobPosting.id)).where(JobPosting.is_active.is_(True))
        ) or 0

        if total_active_jobs == 0:
            return []

        records = []
        for track in self.ROLE_TRACKS:
            keyword = f"%{track}%"
            base_query = select(JobPosting).where(
                JobPosting.is_active.is_(True),
                JobPosting.title.ilike(keyword),
            )

            postings = list(db.scalars(base_query).all())
            count = len(postings)
            if count == 0:
                continue

            market_share = round((count / total_active_jobs) * 100.0, 2)
            remote_count = sum(1 for p in postings if p.is_remote)
            remote_pct = round((remote_count / count) * 100.0, 2)

            # Seniority breakdown
            seniority: dict[str, int] = {e.value: 0 for e in ExperienceLevel}
            for p in postings:
                lvl = p.experience_level.value if hasattr(p.experience_level, "value") else str(p.experience_level)
                if lvl in seniority:
                    seniority[lvl] += 1
                else:
                    seniority[lvl] = 1

            records.append(
                RoleDistributionRecord(
                    role_name=track,
                    total_postings=count,
                    market_share_pct=market_share,
                    seniority_breakdown=seniority,
                    remote_postings_count=remote_count,
                    remote_pct=remote_pct,
                )
            )

        # Sort descending by total postings
        records.sort(key=lambda r: r.total_postings, reverse=True)
        return records


role_analyzer = RoleAnalyzer()
