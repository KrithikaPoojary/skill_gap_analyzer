"""Unit tests for analytics Pydantic schemas."""

import pytest

from app.schemas.analytics import (
    DistributionStatsSchema,
    LocationDistributionSchema,
    MarketOverviewSchema,
    RemoteWorkSummarySchema,
    RoleDistributionSchema,
    SalaryBenchmarkSchema,
    SkillDemandSchema,
)


class TestAnalyticsSchemas:
    """Test suite for analytical model validation and serialization."""

    def test_distribution_stats_schema(self) -> None:
        stats = DistributionStatsSchema(
            count=10,
            mean=50.0,
            std_dev=5.0,
            min=40.0,
            p25=45.0,
            median=50.0,
            p75=55.0,
            p90=58.0,
            max=60.0,
            iqr=10.0,
        )
        assert stats.count == 10
        assert stats.median == 50.0
        dump = stats.model_dump()
        assert dump["iqr"] == 10.0

    def test_skill_demand_schema(self) -> None:
        skill = SkillDemandSchema(
            skill_id=1,
            skill_name="Python",
            category="language",
            total_postings=100,
            market_penetration_pct=80.0,
            mandatory_count=70,
            preferred_count=30,
            avg_importance=1.4,
        )
        assert skill.skill_name == "Python"
        assert skill.market_penetration_pct == 80.0

    def test_market_overview_schema(self) -> None:
        overview = MarketOverviewSchema(
            total_active_jobs=520,
            total_skills_tracked=70,
            overall_remote_pct=42.5,
            top_skills=[],
            top_roles=[],
            top_locations=[],
        )
        assert overview.total_active_jobs == 520
        assert overview.overall_remote_pct == 42.5
