"""Tests for single skill retrieval endpoint."""
from __future__ import annotations

from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.skill import Skill, SkillCategory


class TestSkillGetById:

    def test_get_skill_by_id_success(self, client: TestClient) -> None:
        with SessionLocal() as db:
            skill = Skill(
                name="Kubernetes Orchestration",
                normalized_name="kubernetes-orchestration",
                category=SkillCategory.CLOUD_DEVOPS.value,
            )
            db.add(skill)
            db.commit()
            db.refresh(skill)
            skill_id = skill.id

        response = client.get(f"/api/v1/skills/{skill_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == skill_id
        assert data["name"] == "Kubernetes Orchestration"
        assert data["category"] == SkillCategory.CLOUD_DEVOPS.value

    def test_get_skill_by_id_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/skills/99999999")
        assert response.status_code == 404
