"""Unit tests for Skill entity and taxonomy SQLAlchemy ORM model."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.skill import Skill, SkillCategory


@pytest.fixture
def db_session():
    """Create a temporary in-memory database session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestSkillModel:
    """Test suite for Skill taxonomy model."""

    def test_create_skill(self, db_session: Session) -> None:
        skill = Skill(
            name="FastAPI",
            normalized_name=Skill.normalize("FastAPI"),
            category=SkillCategory.FRAMEWORK.value,
            description="Modern, fast web framework for building APIs with Python.",
            aliases="fast-api, fastapi framework",
        )
        db_session.add(skill)
        db_session.commit()
        db_session.refresh(skill)

        assert skill.id is not None
        assert skill.name == "FastAPI"
        assert skill.normalized_name == "fastapi"
        assert skill.category == "framework"
        assert skill.is_verified is True
        assert "FastAPI" in repr(skill)

    def test_unique_skill_name_constraint(self, db_session: Session) -> None:
        skill1 = Skill(
            name="Python",
            normalized_name="python",
            category=SkillCategory.LANGUAGE.value,
        )
        skill2 = Skill(
            name="Python",
            normalized_name="python",
            category=SkillCategory.LANGUAGE.value,
        )
        db_session.add(skill1)
        db_session.commit()

        db_session.add(skill2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_skill_normalize_helper(self) -> None:
        assert Skill.normalize("  Node.js ") == "nodejs"
        assert Skill.normalize("React-Native") == "react native"
        assert Skill.normalize("TypeScript") == "typescript"

    def test_filter_by_category(self, db_session: Session) -> None:
        skills = [
            Skill(name="Python", normalized_name="python", category=SkillCategory.LANGUAGE.value),
            Skill(name="Go", normalized_name="go", category=SkillCategory.LANGUAGE.value),
            Skill(name="Docker", normalized_name="docker", category=SkillCategory.CLOUD_DEVOPS.value),
            Skill(name="PostgreSQL", normalized_name="postgresql", category=SkillCategory.DATABASE.value),
        ]
        db_session.add_all(skills)
        db_session.commit()

        languages = db_session.query(Skill).filter_by(category=SkillCategory.LANGUAGE.value).all()
        assert len(languages) == 2
        names = {s.name for s in languages}
        assert names == {"Python", "Go"}
