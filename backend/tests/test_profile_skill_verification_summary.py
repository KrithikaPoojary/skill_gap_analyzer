"""Tests for user skill verification summary endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient
from app.db.session import SessionLocal
from app.models.skill import Skill
from app.models.associations import UserSkill
from app.models.user import User


class TestProfileSkillVerificationSummary:
    """Tests for GET /api/v1/profile/me/skills/verification-summary."""

    def test_verification_summary_unauthenticated(self, client: TestClient) -> None:
        res = client.get("/api/v1/profile/me/skills/verification-summary")
        assert res.status_code == 401

    def test_verification_summary_authenticated_flow(self, client: TestClient) -> None:
        suffix = uuid.uuid4().hex[:6]
        email = f"verif_{suffix}@example.com"
        password = "Password123!"

        # Register & login
        client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Verif User"})
        tok_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        token = tok_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Initially 0 skills
        res0 = client.get("/api/v1/profile/me/skills/verification-summary", headers=headers)
        assert res0.status_code == 200
        d0 = res0.json()["data"]
        assert d0["total_skills"] == 0
        assert d0["verified_count"] == 0
        assert d0["unverified_count"] == 0
        assert d0["verification_rate_pct"] == 0.0

        # Create skills in DB and link
        with SessionLocal() as db:
            user = db.query(User).filter_by(email=email).first()
            assert user is not None

            s1 = Skill(name=f"Verified Py {suffix}", normalized_name=f"ver_py_{suffix}", category="languages")
            s2 = Skill(name=f"Unverified Go {suffix}", normalized_name=f"unver_go_{suffix}", category="languages")
            db.add_all([s1, s2])
            db.commit()

            us1 = UserSkill(
                user_id=user.id,
                skill_id=s1.id,
                proficiency_level="expert",
                years_of_experience=4.0,
                is_verified=True,
            )
            us2 = UserSkill(
                user_id=user.id,
                skill_id=s2.id,
                proficiency_level="beginner",
                years_of_experience=1.0,
                is_verified=False,
            )
            db.add_all([us1, us2])
            db.commit()

        res1 = client.get("/api/v1/profile/me/skills/verification-summary", headers=headers)
        assert res1.status_code == 200
        d1 = res1.json()["data"]
        assert d1["total_skills"] == 2
        assert d1["verified_count"] == 1
        assert d1["unverified_count"] == 1
        assert d1["verification_rate_pct"] == 50.0
        assert len(d1["verified_skills"]) == 1
        assert d1["verified_skills"][0]["skill_name"] == f"Verified Py {suffix}"
        assert len(d1["unverified_skills"]) == 1
        assert d1["unverified_skills"][0]["skill_name"] == f"Unverified Go {suffix}"
