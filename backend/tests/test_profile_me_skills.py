"""Tests for GET /profile/me/skills endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.models.associations import UserSkill
from app.models.skill import Skill
from sqlalchemy.orm import Session


class TestProfileMeSkills:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"my_skills_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_get_my_skills_empty(self, client: TestClient) -> None:
        _, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}
        res = client.get("/api/v1/profile/me/skills", headers=headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total"] == 0
        assert data["skills"] == []

    def test_get_my_skills_with_filters(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        with Session(engine) as db:
            uid = uuid.uuid4().hex[:6]
            s1 = Skill(name=f"Rust_{uid}", normalized_name=f"rust_{uid}", category="language")
            s2 = Skill(name=f"Terraform_{uid}", normalized_name=f"terraform_{uid}", category="cloud_devops")
            db.add_all([s1, s2])
            db.flush()

            us1 = UserSkill(user_id=user_id, skill_id=s1.id, proficiency_level="expert", is_verified=True)
            us2 = UserSkill(user_id=user_id, skill_id=s2.id, proficiency_level="beginner", is_verified=False)
            db.add_all([us1, us2])
            db.commit()

        # All skills
        res_all = client.get("/api/v1/profile/me/skills", headers=headers)
        assert res_all.status_code == 200
        assert res_all.json()["data"]["total"] == 2

        # Filter by category
        res_cat = client.get("/api/v1/profile/me/skills?category=language", headers=headers)
        assert res_cat.status_code == 200
        assert res_cat.json()["data"]["total"] == 1
        assert res_cat.json()["data"]["skills"][0]["category"] == "language"

        # Filter by proficiency
        res_prof = client.get("/api/v1/profile/me/skills?proficiency_level=expert", headers=headers)
        assert res_prof.status_code == 200
        assert res_prof.json()["data"]["total"] == 1
        assert res_prof.json()["data"]["skills"][0]["proficiency_level"] == "expert"

        # Filter by verified
        res_ver = client.get("/api/v1/profile/me/skills?is_verified=true", headers=headers)
        assert res_ver.status_code == 200
        assert res_ver.json()["data"]["total"] == 1
        assert res_ver.json()["data"]["skills"][0]["is_verified"] is True
