"""Unit tests for the SalaryAnalyzer service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401
from app.models.associations import JobSkill
from app.models.job import JobPosting
from app.models.skill import Skill
from app.schemas.enums import ExperienceLevel
from app.services.analytics.salary_analyzer import SalaryAnalyzer, salary_analyzer


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
        # Seed test jobs with salary numbers
        j1 = JobPosting(
            title="Junior Backend Engineer",
            company_name="A",
            description="desc",
            min_salary=80000.0,
            max_salary=100000.0,
            experience_level=ExperienceLevel.ENTRY.value,
            is_remote=False,
            is_active=True,
        )
        j2 = JobPosting(
            title="Senior Backend Engineer",
            company_name="B",
            description="desc",
            min_salary=140000.0,
            max_salary=180000.0,
            experience_level=ExperienceLevel.SENIOR.value,
            is_remote=True,
            is_active=True,
        )
        session.add_all([j1, j2])
        session.flush()

        s = Skill(name="Python", normalized_name="python", category="language")
        session.add(s)
        session.flush()

        js1 = JobSkill(job_id=j1.id, skill_id=s.id, is_required=True)
        js2 = JobSkill(job_id=j2.id, skill_id=s.id, is_required=True)
        session.add_all([js1, js2])
        session.commit()

        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestSalaryAnalytics:
    """Test suite for salary benchmarks by experience, role, remote, and skill."""

    def test_get_salary_by_experience(self, db_session) -> None:
        records = salary_analyzer.get_salary_by_experience(db_session)
        assert len(records) == len(ExperienceLevel)

        entry_record = next(r for r in records if r.dimension_value == ExperienceLevel.ENTRY.value)
        assert entry_record.stats.count == 1
        assert entry_record.stats.median == 90000.0

        senior_record = next(r for r in records if r.dimension_value == ExperienceLevel.SENIOR.value)
        assert senior_record.stats.count == 1
        assert senior_record.stats.median == 160000.0

    def test_get_remote_salary_comparison(self, db_session) -> None:
        comp = salary_analyzer.get_remote_salary_comparison(db_session)
        assert comp["remote"].count == 1
        assert comp["remote"].median == 160000.0
        assert comp["onsite"].count == 1
        assert comp["onsite"].median == 90000.0

    def test_get_salary_for_skill(self, db_session) -> None:
        py_salary = salary_analyzer.get_salary_for_skill(db_session, "python")
        assert py_salary.count == 2
        assert py_salary.median == 125000.0
        assert py_salary.min == 90000.0
        assert py_salary.max == 160000.0
