"""Tests for target roles filtered by experience endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.models.role import TargetRole


def test_get_roles_by_experience_filtering(client: TestClient) -> None:
    """GET /roles/by-experience returns roles matching experience and category constraints."""
    suffix = uuid.uuid4().hex[:6]
    cat_soft = f"Software_{suffix}"
    cat_arch = f"Architecture_{suffix}"

    with SessionLocal() as db:
        role_junior = TargetRole(
            title=f"Junior Dev {suffix}",
            slug=f"junior-dev-{suffix}",
            category=cat_soft,
            min_experience_years=1,
            is_active=True,
        )
        role_mid = TargetRole(
            title=f"Mid Dev {suffix}",
            slug=f"mid-dev-{suffix}",
            category=cat_soft,
            min_experience_years=3,
            is_active=True,
        )
        role_senior = TargetRole(
            title=f"Senior Architect {suffix}",
            slug=f"senior-arch-{suffix}",
            category=cat_arch,
            min_experience_years=7,
            is_active=True,
        )
        db.add_all([role_junior, role_mid, role_senior])
        db.commit()
        db.refresh(role_junior)
        db.refresh(role_mid)
        db.refresh(role_senior)

    # Filter min_exp=2 and max_exp=5 for the specific test category
    resp = client.get(f"/api/v1/roles/by-experience?min_exp=2&max_exp=5&category={cat_soft}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    role_ids = [r["id"] for r in data["roles"]]
    assert role_mid.id in role_ids
    assert role_junior.id not in role_ids
    assert role_senior.id not in role_ids

    # Filter by architecture category
    resp_cat = client.get(f"/api/v1/roles/by-experience?category={cat_arch}")
    assert resp_cat.status_code == 200
    cat_roles = resp_cat.json()["data"]["roles"]
    cat_role_ids = [r["id"] for r in cat_roles]
    assert role_senior.id in cat_role_ids
    assert role_mid.id not in cat_role_ids
