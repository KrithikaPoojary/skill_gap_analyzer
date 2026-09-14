"""Geographic distribution and remote-work analytics service.

Computes job concentration across geographical tech hubs, remote eligibility ratios,
and location-based market share breakdowns.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app.models.job import JobPosting
from app.schemas.enums import ExperienceLevel


@dataclass(frozen=True)
class LocationDistributionRecord:
    """Market concentration metrics for an individual city or region."""

    location_name: str
    total_postings: int
    market_share_pct: float
    remote_postings_count: int
    remote_pct: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RemoteWorkSummary:
    """Overall and segmented remote-work ratio metrics."""

    total_active_jobs: int
    total_remote_jobs: int
    overall_remote_pct: float
    remote_by_seniority: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GeoAnalyzer:
    """Analyzes location distribution and remote work dynamics."""

    def get_top_locations(
        self,
        db: Session,
        *,
        limit: int = 15,
    ) -> list[LocationDistributionRecord]:
        """Compute top hiring locations ordered by job volume."""
        total_active_jobs = db.scalar(
            select(func.count(JobPosting.id)).where(JobPosting.is_active.is_(True))
        ) or 0

        if total_active_jobs == 0:
            return []

        stmt = (
            select(
                func.coalesce(JobPosting.location, "Unspecified").label("loc"),
                func.count(JobPosting.id).label("total"),
                func.sum(case((JobPosting.is_remote.is_(True), 1), else_=0)).label("remote_cnt"),
            )
            .where(JobPosting.is_active.is_(True))
            .group_by("loc")
            .order_by(desc("total"))
            .limit(limit)
        )

        rows = db.execute(stmt).all()
        records = []
        for loc, total, rem_cnt in rows:
            tot = int(total or 0)
            rem = int(rem_cnt or 0)
            share = round((tot / total_active_jobs) * 100.0, 2)
            rem_pct = round((rem / tot) * 100.0, 2) if tot > 0 else 0.0

            records.append(
                LocationDistributionRecord(
                    location_name=loc,
                    total_postings=tot,
                    market_share_pct=share,
                    remote_postings_count=rem,
                    remote_pct=rem_pct,
                )
            )

        return records

    def get_remote_summary(self, db: Session) -> RemoteWorkSummary:
        """Calculate overall remote work percentage and breakdown by seniority level."""
        total_active_jobs = db.scalar(
            select(func.count(JobPosting.id)).where(JobPosting.is_active.is_(True))
        ) or 0

        if total_active_jobs == 0:
            return RemoteWorkSummary(
                total_active_jobs=0,
                total_remote_jobs=0,
                overall_remote_pct=0.0,
                remote_by_seniority={},
            )

        total_remote = db.scalar(
            select(func.count(JobPosting.id)).where(
                JobPosting.is_active.is_(True),
                JobPosting.is_remote.is_(True),
            )
        ) or 0

        overall_pct = round((total_remote / total_active_jobs) * 100.0, 2)

        # Breakdown by seniority
        by_seniority: dict[str, float] = {}
        for level in ExperienceLevel:
            lvl_total = db.scalar(
                select(func.count(JobPosting.id)).where(
                    JobPosting.is_active.is_(True),
                    JobPosting.experience_level == level.value,
                )
            ) or 0

            lvl_remote = db.scalar(
                select(func.count(JobPosting.id)).where(
                    JobPosting.is_active.is_(True),
                    JobPosting.experience_level == level.value,
                    JobPosting.is_remote.is_(True),
                )
            ) or 0

            ratio = round((lvl_remote / lvl_total) * 100.0, 2) if lvl_total > 0 else 0.0
            by_seniority[level.value] = ratio

        return RemoteWorkSummary(
            total_active_jobs=total_active_jobs,
            total_remote_jobs=total_remote,
            overall_remote_pct=overall_pct,
            remote_by_seniority=by_seniority,
        )


geo_analyzer = GeoAnalyzer()
