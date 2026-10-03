"""Tests for popular target roles leaderboard endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import TargetRole, UserTargetRole
from app.models.user import User


def test_get_popular_target_roles(client: TestClient) -> None:
    """GET /roles/popular returns roles sorted by tracking count."""
    suffix = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        role1 = TargetRole(
            title=f"Cloud Architect {suffix}",
            slug=f"cloud-architect-{suffix}",
            category="Cloud",
            is_active=True,
        )
        role2 = TargetRole(
            title=f"QA Engineer {suffix}",
            slug=f"qa-engineer-{suffix}",
            category="Quality",
            is_active=True,
        )
        u1 = User(email=f"pop1_{suffix}@test.com", hashed_password="pw")
        u2 = User(email=f"pop2_{suffix}@test.com", hashed_password="pw")
        db.add_all([role1, role2, u1, u2])
        db.commit()
        db.refresh(role1)
        db.refresh(role2)
        db.refresh(u1)
        db.refresh(u2)

        # 2 users track role1, 0 users track role2
        ut1 = UserTargetRole(user_id=u1.id, role_id=role1.id)
        ut2 = UserTargetRole(user_id=u2.id, role_id=role1.id)
        db.add_all([ut1, ut2])
        db.commit()

    resp = client.get("/api/v1/roles/popular?limit=20")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 2

    # Find role1 in the list
    r1_item = next(r for r in data if r["id"] == role1.id)
    assert r1_item["candidates_tracking"] == 2
