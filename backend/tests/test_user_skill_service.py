"""Unit tests for UserSkillService."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.skill import Skill
from app.models.user import User
from app.services.user_skill_service import user_skill_service


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Seed a test user."""
    user = User(
        email="test_engineer@example.com",
        hashed_password="hash_secret_value",
        full_name="Alice Engineer",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seed_skills(db_session: Session) -> list[Skill]:
    """Seed sample skills into taxonomy."""
    skills = [
        Skill(name="Python", normalized_name="python", category="language"),
        Skill(name="FastAPI", normalized_name="fastapi", category="framework"),
        Skill(name="Docker", normalized_name="docker", category="cloud_devops"),
    ]
    db_session.add_all(skills)
    db_session.commit()
    return skills


class TestUserSkillService:
    def test_add_skill_by_id(self, db_session: Session, test_user: User, seed_skills: list[Skill]):
        py_skill = seed_skills[0]
        user_skill = user_skill_service.add_user_skill(
            db_session,
            user_id=test_user.id,
            skill_id=py_skill.id,
            proficiency_level="expert",
            years_of_experience=4.5,
            is_verified=True,
        )
        assert user_skill.user_id == test_user.id
        assert user_skill.skill_id == py_skill.id
        assert user_skill.proficiency_level == "expert"
        assert user_skill.years_of_experience == 4.5
        assert user_skill.is_verified is True

    def test_add_skill_by_name_existing(self, db_session: Session, test_user: User, seed_skills: list[Skill]):
        user_skill = user_skill_service.add_user_skill(
            db_session,
            user_id=test_user.id,
            skill_name="FastAPI",
            proficiency_level="advanced",
            years_of_experience=2.0,
        )
        assert user_skill.skill.name == "FastAPI"
        assert user_skill.proficiency_level == "advanced"

    def test_add_skill_by_name_adhoc_auto_creates(self, db_session: Session, test_user: User):
        user_skill = user_skill_service.add_user_skill(
            db_session,
            user_id=test_user.id,
            skill_name="LangChain",
            proficiency_level="beginner",
            years_of_experience=0.5,
        )
        assert user_skill.skill.name == "LangChain"
        assert user_skill.skill.category == "other"
        assert user_skill.skill.is_verified is False

    def test_add_skill_nonexistent_user_raises(self, db_session: Session, seed_skills: list[Skill]):
        with pytest.raises(ValueError, match="User with ID 999 not found"):
            user_skill_service.add_user_skill(
                db_session,
                user_id=999,
                skill_id=seed_skills[0].id,
            )

    def test_add_skill_missing_args_raises(self, db_session: Session, test_user: User):
        with pytest.raises(ValueError, match="Either skill_id or skill_name"):
            user_skill_service.add_user_skill(
                db_session,
                user_id=test_user.id,
            )

    def test_add_skill_updates_existing_record(self, db_session: Session, test_user: User, seed_skills: list[Skill]):
        py_skill = seed_skills[0]
        user_skill_service.add_user_skill(
            db_session,
            user_id=test_user.id,
            skill_id=py_skill.id,
            proficiency_level="beginner",
            years_of_experience=1.0,
        )
        updated = user_skill_service.add_user_skill(
            db_session,
            user_id=test_user.id,
            skill_id=py_skill.id,
            proficiency_level="expert",
            years_of_experience=5.0,
            is_verified=True,
        )
        assert updated.proficiency_level == "expert"
        assert updated.years_of_experience == 5.0
        assert updated.is_verified is True

    def test_get_user_skills_and_names(self, db_session: Session, test_user: User, seed_skills: list[Skill]):
        user_skill_service.add_user_skill(db_session, user_id=test_user.id, skill_name="Python")
        user_skill_service.add_user_skill(db_session, user_id=test_user.id, skill_name="Docker")

        skills = user_skill_service.get_user_skills(db_session, user_id=test_user.id)
        assert len(skills) == 2

        names = user_skill_service.get_user_skill_names(db_session, user_id=test_user.id)
        assert set(names) == {"Python", "Docker"}

    def test_remove_user_skill(self, db_session: Session, test_user: User, seed_skills: list[Skill]):
        py_skill = seed_skills[0]
        user_skill_service.add_user_skill(db_session, user_id=test_user.id, skill_id=py_skill.id)

        removed = user_skill_service.remove_user_skill(db_session, user_id=test_user.id, skill_id=py_skill.id)
        assert removed is True

        removed_again = user_skill_service.remove_user_skill(db_session, user_id=test_user.id, skill_id=py_skill.id)
        assert removed_again is False

    def test_bulk_add_user_skills(self, db_session: Session, test_user: User):
        skills = ["Python", "FastAPI", "Docker", "Kubernetes"]
        added = user_skill_service.bulk_add_user_skills(
            db_session,
            user_id=test_user.id,
            skill_names=skills,
            proficiency_level="intermediate",
        )
        assert len(added) == 4
        names = user_skill_service.get_user_skill_names(db_session, user_id=test_user.id)
        assert set(names) == set(skills)
