"""Tests for skill categories endpoint."""

from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.skill import Skill, SkillCategory


def test_list_skill_categories(client: TestClient) -> None:
    """GET /skills/categories returns all categories with labels and counts."""
    with SessionLocal() as db:
        # Add test skill if not present
        existing = db.query(Skill).filter_by(name="FastAPI_Cat_Test").first()
        if not existing:
            s = Skill(
                name="FastAPI_Cat_Test",
                normalized_name="fastapi_cat_test",
                category=SkillCategory.FRAMEWORK.value,
            )
            db.add(s)
            db.commit()

    response = client.get("/api/v1/skills/categories")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    categories = payload["data"]
    assert len(categories) >= len(SkillCategory)

    framework_cat = next(c for c in categories if c["category"] == "framework")
    assert framework_cat["label"] == "Framework"
    assert framework_cat["skill_count"] >= 1
