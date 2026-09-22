"""Unit tests for SavedJobRepository."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.job import JobPosting
from app.models.saved_job import ApplicationStatus
from app.models.user import User
from app.repositories.saved_job_repo import saved_job_repository


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = User(email="repo_user@example.com", hashed_password="pw")
    job1 = JobPosting(
        title="Dev 1", company_name="Co 1", description="desc 1",
        employment_type="full_time", experience_level="mid"
    )
    job2 = JobPosting(
        title="Dev 2", company_name="Co 2", description="desc 2",
        employment_type="full_time", experience_level="senior"
    )
    session.add_all([user, job1, job2])
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_save_and_list_saved_jobs(db_session):
    saved1 = saved_job_repository.save_job(db_session, user_id=1, job_id=1, notes="Top choice")
    assert saved1.id is not None
    assert saved1.status == ApplicationStatus.SAVED
    assert saved1.notes == "Top choice"

    # Save job2
    saved_job_repository.save_job(db_session, user_id=1, job_id=2)

    jobs = saved_job_repository.list_by_user(db_session, user_id=1)
    assert len(jobs) == 2
    count = saved_job_repository.count_by_user(db_session, user_id=1)
    assert count == 2


def test_update_status_and_remove(db_session):
    saved_job_repository.save_job(db_session, user_id=1, job_id=1)

    updated = saved_job_repository.update_status(
        db_session,
        user_id=1,
        job_id=1,
        status=ApplicationStatus.APPLIED,
        notes="Applied via LinkedIn",
    )
    assert updated is not None
    assert updated.status == ApplicationStatus.APPLIED
    assert updated.applied_at is not None

    # Remove
    removed = saved_job_repository.remove_saved_job(db_session, user_id=1, job_id=1)
    assert removed is True
    assert saved_job_repository.get_by_user_and_job(db_session, user_id=1, job_id=1) is None
