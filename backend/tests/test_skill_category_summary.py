"""Tests for skill category summary and per-category listing endpoints."""

import uuid

from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.skill import Skill, SkillCategory


class TestSkillCategorySummary:
    """Tests for GET /api/v1/skills/categories/summary."""

    def test_category_summary_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/skills/categories/summary")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["success"] is True
        data = payload["data"]
        assert "total_skills" in data
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_category_summary_has_correct_shape(self, client: TestClient) -> None:
        resp = client.get("/api/v1/skills/categories/summary")
        data = resp.json()["data"]
        if len(data["categories"]) > 0:
            cat = data["categories"][0]
            assert "category" in cat
            assert "count" in cat
            assert isinstance(cat["count"], int)


class TestSkillsByCategory:
    """Tests for GET /api/v1/skills/categories/{category}/skills."""

    def test_skills_by_category_returns_200(self, client: TestClient) -> None:
        uid = uuid.uuid4().hex[:8]
        with SessionLocal() as db:
            s = Skill(
                name=f"CatTestSkill_{uid}",
                normalized_name=f"cattestskill_{uid}",
                category=SkillCategory.TESTING.value,
            )
            db.add(s)
            db.commit()

        resp = client.get("/api/v1/skills/categories/testing/skills")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["category"] == "testing"
        assert data["total"] >= 1
        assert isinstance(data["skills"], list)

    def test_skills_by_category_pagination(self, client: TestClient) -> None:
        resp = client.get("/api/v1/skills/categories/language/skills?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_skills_by_empty_category_returns_zero(self, client: TestClient) -> None:
        resp = client.get("/api/v1/skills/categories/nonexistent_cat_xyz/skills")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0
        assert data["skills"] == []
