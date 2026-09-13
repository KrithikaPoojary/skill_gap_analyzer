"""Unit tests for the SkillNormalizer service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.skill import Skill, SkillCategory
from app.services.skill_normalizer import SkillNormalizer, normalize_text, skill_normalizer


@pytest.fixture
def db_session():
    """Isolated in-memory database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestSkillNormalizer:
    """Test suite for skill name normalization, alias resolution, and DB upsert."""

    def test_normalize_text_basic(self) -> None:
        assert normalize_text("  Python  ") == "python"
        assert normalize_text("React.js") == "react.js"
        assert normalize_text("Fast-API") == "fast api"
        assert normalize_text("C++") == "c++"
        assert normalize_text("C#") == "c#"

    @pytest.mark.parametrize(
        ("input_alias", "expected_canonical", "expected_category"),
        [
            ("py", "Python", SkillCategory.LANGUAGE),
            ("python3", "Python", SkillCategory.LANGUAGE),
            ("js", "JavaScript", SkillCategory.LANGUAGE),
            ("golang", "Go", SkillCategory.LANGUAGE),
            ("k8s", "Kubernetes", SkillCategory.CLOUD_DEVOPS),
            ("reactjs", "React", SkillCategory.FRAMEWORK),
            ("react.js", "React", SkillCategory.FRAMEWORK),
            ("postgres", "PostgreSQL", SkillCategory.DATABASE),
            ("amazon web services", "AWS", SkillCategory.CLOUD_DEVOPS),
            ("gcp", "GCP", SkillCategory.CLOUD_DEVOPS),
            ("ml", "Machine Learning", SkillCategory.AI_ML),
            ("docker containers", "Docker", SkillCategory.CLOUD_DEVOPS),
        ],
    )
    def test_known_alias_resolution(
        self,
        input_alias: str,
        expected_canonical: str,
        expected_category: SkillCategory,
    ) -> None:
        canonical, slug, category = skill_normalizer.normalize(input_alias)
        assert canonical == expected_canonical
        assert category == expected_category

    def test_unknown_skill_resolution(self) -> None:
        canonical, slug, category = skill_normalizer.normalize("specialized proprietary tool")
        assert canonical == "Specialized Proprietary Tool"
        assert slug == "specialized proprietary tool"
        assert category == SkillCategory.OTHER

    def test_resolve_or_create_persists_to_db(self, db_session) -> None:
        skill = skill_normalizer.resolve_or_create(db_session, "k8s")
        db_session.commit()

        assert skill.id is not None
        assert skill.name == "Kubernetes"
        assert skill.category == SkillCategory.CLOUD_DEVOPS.value
        assert "k8s" in (skill.aliases or "")

        # Calling again should return the exact same entity without creating duplicate
        skill_again = skill_normalizer.resolve_or_create(db_session, "kubernetes")
        assert skill_again.id == skill.id
        assert db_session.query(Skill).count() == 1
