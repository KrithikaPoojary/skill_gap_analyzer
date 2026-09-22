"""Unit tests for UserSavedJob model and application status lifecycle."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.job import JobPosting
from app.models.saved_job import ApplicationStatus, UserSavedJob
from app.models.user import User


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
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_user_saved_job_lifecycle(db_session):
    user = User(email="test@example.com", hashed_password="pw")
    job = JobPosting(
        title="Python Dev",
        company_name="Tech Co",
        location="Remote",
        is_remote=True,
        employment_type="full_time",
        experience_level="mid",
        description="Build Python backends and APIs.",
    )
    db_session.add_all([user, job])
    db_session.commit()

    saved = UserSavedJob(
        user_id=user.id,
        job_id=job.id,
        status=ApplicationStatus.SAVED,
        notes="Looks like a great team match.",
    )
    db_session.add(saved)
    db_session.commit()
    db_session.refresh(saved)

    assert saved.id is not None
    assert saved.status == ApplicationStatus.SAVED
    assert saved.notes == "Looks like a great team match."
    assert repr(saved) == f"<UserSavedJob user_id={user.id} job_id={job.id} status=saved>"

    # Update status to applied
    saved.status = ApplicationStatus.APPLIED
    db_session.commit()
    db_session.refresh(saved)
    assert saved.status == ApplicationStatus.APPLIED
