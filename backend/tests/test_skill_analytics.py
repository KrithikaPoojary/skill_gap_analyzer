"""Unit tests for the SkillAnalyzer service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401
from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill, SkillCategory
from app.services.analytics.skill_analyzer import SkillAnalyzer, skill_analyzer


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        # Seed test data
        s1 = Skill(name="Python", normalized_name="python", category=SkillCategory.LANGUAGE.value)
        s2 = Skill(name="FastAPI", normalized_name="fastapi", category=SkillCategory.FRAMEWORK.value)
        s3 = Skill(name="AWS", normalized_name="aws", category=SkillCategory.CLOUD_DEVOPS.value)
        session.add_all([s1, s2, s3])
        session.flush()

        j1 = JobPosting(title="Backend Dev 1", company_name="Company A", description="Desc 1", is_active=True)
        j2 = JobPosting(title="Backend Dev 2", company_name="Company B", description="Desc 2", is_active=True)
        session.add_all([j1, j2])
        session.flush()

        # Both jobs require Python, j1 requires FastAPI, j2 prefers AWS
        js1 = JobSkill(job_id=j1.id, skill_id=s1.id, is_required=True, importance_weight=1.5)
        js2 = JobSkill(job_id=j1.id, skill_id=s2.id, is_required=True, importance_weight=1.2)
        js3 = JobSkill(job_id=j2.id, skill_id=s1.id, is_required=True, importance_weight=1.8)
        js4 = JobSkill(job_id=j2.id, skill_id=s3.id, is_required=False, importance_weight=0.8)
        session.add_all([js1, js2, js3, js4])
        session.commit()

        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestSkillAnalytics:
    """Test suite for top skills ranking, penetration calculation, and categories."""

    def test_get_top_skills_ranking(self, db_session) -> None:
        top = skill_analyzer.get_top_skills(db_session, limit=10)
        assert len(top) == 3
        # Python is in both jobs (100% penetration)
        assert top[0].skill_name == "Python"
        assert top[0].total_postings == 2
        assert top[0].market_penetration_pct == 100.0
        assert top[0].mandatory_count == 2
        assert top[0].preferred_count == 0

    def test_get_top_skills_filtered_by_category(self, db_session) -> None:
        frameworks = skill_analyzer.get_top_skills(
            db_session,
            category=SkillCategory.FRAMEWORK,
        )
        assert len(frameworks) == 1
        assert frameworks[0].skill_name == "FastAPI"
        assert frameworks[0].total_postings == 1
        assert frameworks[0].market_penetration_pct == 50.0

    def test_get_category_distribution(self, db_session) -> None:
        cat_dist = skill_analyzer.get_category_distribution(db_session)
        assert cat_dist[SkillCategory.LANGUAGE.value] == 2
        assert cat_dist[SkillCategory.FRAMEWORK.value] == 1
        assert cat_dist[SkillCategory.CLOUD_DEVOPS.value] == 1
