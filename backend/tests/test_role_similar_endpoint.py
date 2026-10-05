"""Tests for similar roles recommendation endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import TargetRole


def test_get_similar_roles(client: TestClient) -> None:
    """GET /roles/{role_id}/similar returns active roles in the same category excluding self."""
    suffix = uuid.uuid4().hex[:6]
    cat = f"AI_Category_{suffix}"

    with SessionLocal() as db:
        role1 = TargetRole(
            title=f"ML Engineer {suffix}",
            slug=f"ml-eng-{suffix}",
            category=cat,
            is_active=True,
        )
        role2 = TargetRole(
            title=f"Data Scientist {suffix}",
            slug=f"data-sci-{suffix}",
            category=cat,
            is_active=True,
        )
        role3 = TargetRole(
            title=f"Deep Learning Researcher {suffix}",
            slug=f"dl-researcher-{suffix}",
            category=cat,
            is_active=True,
        )
        other_cat_role = TargetRole(
            title=f"Web Dev {suffix}",
            slug=f"web-dev-{suffix}",
            category=f"Other_{suffix}",
            is_active=True,
        )
        db.add_all([role1, role2, role3, other_cat_role])
        db.commit()
        db.refresh(role1)
        db.refresh(role2)
        db.refresh(role3)

    resp = client.get(f"/api/v1/roles/{role1.id}/similar")
    assert resp.status_code == 200
    res_data = resp.json()["data"]
    assert res_data["role_id"] == role1.id
    assert res_data["category"] == cat

    similar_titles = [r["title"] for r in res_data["similar_roles"]]
    assert role2.title in similar_titles
    assert role3.title in similar_titles
    assert role1.title not in similar_titles
    assert other_cat_role.title not in similar_titles


def test_get_similar_roles_not_found(client: TestClient) -> None:
    """GET /roles/{role_id}/similar returns 404 for non-existent role."""
    resp = client.get("/api/v1/roles/99999999/similar")
    assert resp.status_code == 404
