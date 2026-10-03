"""End-to-end integration test validating the entire user journey:
Register -> Login -> Upsert Profile -> Add Skills -> Update Skills -> Generate Roadmap -> Check Progress -> Notification Badging.
"""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import TargetRole, RoleSkillWeighting
from app.models.skill import Skill, SkillCategory


class TestUserCompleteJourney:

    def test_full_candidate_lifecycle(self, client: TestClient) -> None:
        tag = uuid.uuid4().hex[:6]
        email = f"journey_{tag}@example.com"
        password = "JourneyPass123!"

        # 1. Register candidate account
        reg_resp = client.post("/api/v1/auth/register", json={"email": email, "password": password})
        assert reg_resp.status_code == 201
        user_id = reg_resp.json()["id"]

        # 2. Login to obtain access token
        login_resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Complete profile metadata
        prof_resp = client.put(
            "/api/v1/profile/me",
            json={
                "headline": "Full-Stack Software Engineer",
                "bio": "Passionate about cloud architecture and distributed systems.",
                "current_title": "Software Engineer",
                "years_of_experience": 3.5,
                "location": "San Francisco, CA",
            },
            headers=headers,
        )
        assert prof_resp.status_code == 200
        assert prof_resp.json()["data"]["headline"] == "Full-Stack Software Engineer"

        # 4. Create taxonomy skills & role
        with SessionLocal() as db:
            s1 = Skill(name=f"Python {tag}", normalized_name=f"python-{tag}", category=SkillCategory.LANGUAGE.value)
            s2 = Skill(name=f"FastAPI {tag}", normalized_name=f"fastapi-{tag}", category=SkillCategory.FRAMEWORK.value)
            s3 = Skill(name=f"Docker {tag}", normalized_name=f"docker-{tag}", category=SkillCategory.CLOUD_DEVOPS.value)
            db.add_all([s1, s2, s3])
            db.commit()
            db.refresh(s1)
            db.refresh(s2)
            db.refresh(s3)

            role = TargetRole(title=f"Backend Lead {tag}", slug=f"backend-lead-{tag}", description="Lead backend engineer")
            db.add(role)
            db.commit()
            db.refresh(role)

            w1 = RoleSkillWeighting(role_id=role.id, skill_id=s1.id, weight=4.0, is_core=True, benchmark_level="advanced")
            w2 = RoleSkillWeighting(role_id=role.id, skill_id=s2.id, weight=3.0, is_core=True, benchmark_level="intermediate")
            w3 = RoleSkillWeighting(role_id=role.id, skill_id=s3.id, weight=2.0, is_core=False, benchmark_level="intermediate")
            db.add_all([w1, w2, w3])
            db.commit()

            s1_id = s1.id
            role_id = role.id

        # 5. Add skills to candidate profile
        add_s1 = client.post(
            "/api/v1/profile/me/skills",
            json={"skill_id": s1_id, "proficiency_level": "intermediate", "years_of_experience": 2.0},
            headers=headers,
        )
        assert add_s1.status_code == 201

        # 6. Update skill proficiency
        update_s1 = client.patch(
            f"/api/v1/profile/me/skills/{s1_id}",
            json={"proficiency_level": "advanced", "years_of_experience": 4.0},
            headers=headers,
        )
        assert update_s1.status_code == 200
        assert update_s1.json()["data"]["proficiency_level"] == "advanced"

        # 7. Check user profile stats
        stats_resp = client.get("/api/v1/profile/me/stats", headers=headers)
        assert stats_resp.status_code == 200
        assert stats_resp.json()["data"]["total_skills"] >= 1

        # 8. Generate personalized learning roadmap
        rm_resp = client.post(
            "/api/v1/roadmaps/me",
            params={"role_id": role_id, "weekly_commitment_hours": 12},
            headers=headers,
        )
        assert rm_resp.status_code == 201
        roadmap_id = rm_resp.json()["data"]["id"]

        # 9. Get roadmap details
        rm_detail_resp = client.get(f"/api/v1/roadmaps/me/{roadmap_id}", headers=headers)
        assert rm_detail_resp.status_code == 200
        assert rm_detail_resp.json()["data"]["id"] == roadmap_id
        assert rm_detail_resp.json()["data"]["user_id"] == user_id

        # 10. Check aggregated progress summary
        progress_resp = client.get("/api/v1/roadmaps/me/progress", headers=headers)
        assert progress_resp.status_code == 200
        assert progress_resp.json()["data"]["total_roadmaps"] >= 1

        # 11. Check unread notifications count
        notif_resp = client.get("/api/v1/notifications/unread-count", headers=headers)
        assert notif_resp.status_code == 200
        assert notif_resp.json()["unread_count"] == 0
