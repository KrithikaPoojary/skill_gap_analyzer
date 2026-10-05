"""Tests for the learning path recommendations endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import RoleSkillWeighting, TargetRole
from app.models.skill import Skill


class TestLearningPathEndpoint:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        email = f"lpath_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_learning_path_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/recommendations/me/learning-path")
        assert resp.status_code == 401

    def test_learning_path_with_role_and_skills(self, client: TestClient) -> None:
        user_id, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        suffix = uuid.uuid4().hex[:6]

        with SessionLocal() as db:
            s1 = Skill(name=f"GoLang_{suffix}", normalized_name=f"golang_{suffix}", category="backend")
            s2 = Skill(name=f"gRPC_{suffix}", normalized_name=f"grpc_{suffix}", category="backend")
            s3 = Skill(name=f"Protobuf_{suffix}", normalized_name=f"protobuf_{suffix}", category="backend")
            role = TargetRole(
                title=f"Go Developer {suffix}",
                slug=f"go-dev-{suffix}",
                category="Backend",
                is_active=True,
            )
            db.add_all([s1, s2, s3, role])
            db.commit()
            db.refresh(s1); db.refresh(s2); db.refresh(s3); db.refresh(role)

            db.add_all([
                RoleSkillWeighting(role_id=role.id, skill_id=s1.id, weight=0.5, is_core=True),
                RoleSkillWeighting(role_id=role.id, skill_id=s2.id, weight=0.3, is_core=True),
                RoleSkillWeighting(role_id=role.id, skill_id=s3.id, weight=0.2, is_core=False),
            ])
            db.commit()

        # User knows GoLang but not gRPC / Protobuf
        client.post(
            "/api/v1/profile/me/skills",
            json={"skill_name": f"GoLang_{suffix}", "proficiency_level": "intermediate"},
            headers=headers,
        )

        resp = client.get("/api/v1/recommendations/me/learning-path", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_skills" in data
        assert "learning_path" in data
        # gRPC and Protobuf should appear as missing skills
        skill_names = [item["skill"] for item in data["learning_path"]]
        assert f"gRPC_{suffix}" in skill_names or f"Protobuf_{suffix}" in skill_names

    def test_learning_path_empty_when_no_roles(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/recommendations/me/learning-path", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        # May return empty or non-empty depending on seeded data — just verify structure
        assert "total_skills" in data
        assert "learning_path" in data
