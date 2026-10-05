"""Tests for role search filter and GET /roles/categories endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.models.role import TargetRole
from sqlalchemy.orm import Session


class TestRoleCategoriesAndSearch:

    def test_role_categories_and_search(self, client: TestClient) -> None:
        with Session(engine) as db:
            uid = uuid.uuid4().hex[:6]
            r1 = TargetRole(
                title=f"Machine Learning Specialist {uid}",
                slug=f"ml-spec-{uid}",
                category=f"AI & Data {uid}",
                description="Deep learning and NLP engineering",
                is_active=True,
            )
            r2 = TargetRole(
                title=f"Cloud Solutions Architect {uid}",
                slug=f"cloud-arch-{uid}",
                category=f"Cloud Infrastructure {uid}",
                description="AWS and multi-cloud systems",
                is_active=True,
            )
            db.add_all([r1, r2])
            db.commit()

        # 1. Test Categories endpoint
        res_cats = client.get("/api/v1/roles/categories")
        assert res_cats.status_code == 200
        data_cats = res_cats.json()["data"]
        cat_names = [c["category"] for c in data_cats]
        assert f"AI & Data {uid}" in cat_names
        assert f"Cloud Infrastructure {uid}" in cat_names

        # 2. Test keyword search endpoint
        res_search = client.get(f"/api/v1/roles?q=Machine Learning Specialist {uid}")
        assert res_search.status_code == 200
        items = res_search.json()["data"]
        assert len(items) == 1
        assert items[0]["slug"] == f"ml-spec-{uid}"

        # 3. Test search by description
        res_desc = client.get("/api/v1/roles?q=multi-cloud systems")
        assert res_desc.status_code == 200
        items_desc = res_desc.json()["data"]
        assert len(items_desc) >= 1
