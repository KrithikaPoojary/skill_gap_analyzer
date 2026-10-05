"""Tests for the skill search autocomplete endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.skill import Skill


class TestSkillSearchEndpoint:

    def _seed_skill(self, suffix: str, name: str, category: str = "backend") -> Skill:
        with SessionLocal() as db:
            skill = Skill(
                name=f"{name}_{suffix}",
                normalized_name=f"{name.lower()}_{suffix}",
                category=category,
            )
            db.add(skill)
            db.commit()
            db.refresh(skill)
            return skill

    def test_search_returns_matching_skills(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        self._seed_skill(suffix, "ElasticSearch", "data")

        resp = client.get("/api/v1/skills/search", params={"q": f"ElasticSearch_{suffix}"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert any(s["name"] == f"ElasticSearch_{suffix}" for s in data)

    def test_search_with_category_filter(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        self._seed_skill(suffix, "Kafka", "backend")

        resp = client.get("/api/v1/skills/search", params={"q": f"Kafka_{suffix}", "category": "backend"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        matching = [s for s in data if s["name"] == f"Kafka_{suffix}"]
        assert len(matching) == 1
        assert matching[0]["category"] == "backend"

    def test_search_missing_q_returns_422(self, client: TestClient) -> None:
        resp = client.get("/api/v1/skills/search")
        assert resp.status_code == 422

    def test_search_no_match_returns_empty_list(self, client: TestClient) -> None:
        resp = client.get("/api/v1/skills/search", params={"q": "xyznonexistent_skill_9999"})
        assert resp.status_code == 200
        assert resp.json()["data"] == []
