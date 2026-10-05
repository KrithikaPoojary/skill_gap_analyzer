"""Tests for popular skills endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.associations import UserSkill
from app.models.skill import Skill
from app.models.user import User


def test_get_popular_skills(client: TestClient) -> None:
    """GET /skills/popular returns skills ranked by candidate count."""
    suffix = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        s1 = Skill(name=f"Python_{suffix}", normalized_name=f"python_{suffix}", category="backend")
        s2 = Skill(name=f"React_{suffix}", normalized_name=f"react_{suffix}", category="frontend")
        u1 = User(email=f"popskill1_{suffix}@test.com", hashed_password="pw")
        u2 = User(email=f"popskill2_{suffix}@test.com", hashed_password="pw")
        db.add_all([s1, s2, u1, u2])
        db.commit()
        db.refresh(s1)
        db.refresh(s2)
        db.refresh(u1)
        db.refresh(u2)

        # 2 users adopt s1, 0 users adopt s2
        us1 = UserSkill(user_id=u1.id, skill_id=s1.id, proficiency_level="expert")
        us2 = UserSkill(user_id=u2.id, skill_id=s1.id, proficiency_level="intermediate")
        db.add_all([us1, us2])
        db.commit()

    resp = client.get("/api/v1/skills/popular?limit=50")
    assert resp.status_code == 200
    skills = resp.json()["data"]
    s1_item = next(item for item in skills if item["id"] == s1.id)
    assert s1_item["candidate_count"] == 2
    assert s1_item["name"] == f"Python_{suffix}"
