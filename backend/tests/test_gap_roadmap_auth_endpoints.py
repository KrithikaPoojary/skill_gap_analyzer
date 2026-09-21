"""Tests for authenticated gap-analysis and roadmaps /me endpoints."""
import uuid
from starlette.testclient import TestClient


class TestGapAnalysisMeEndpoint:

    def _tok(self, c: TestClient) -> str:
        e = f"g{uuid.uuid4().hex[:6]}@x.com"
        c.post("/api/v1/auth/register", json={"email": e, "password": "P@ss123!", "full_name": "T"})
        return c.post("/api/v1/auth/login", data={"username": e, "password": "P@ss123!"}).json()["access_token"]

    def test_unauth_401(self, client: TestClient):
        assert client.get("/api/v1/gap-analysis/me").status_code == 401

    def test_no_role_400(self, client: TestClient):
        t = self._tok(client)
        assert client.get("/api/v1/gap-analysis/me", headers={"Authorization": f"Bearer {t}"}).status_code == 400

    def test_with_role_200(self, client: TestClient):
        t = self._tok(client)
        r = client.get("/api/v1/gap-analysis/me", params={"role_name": "Developer"}, headers={"Authorization": f"Bearer {t}"})
        assert r.status_code == 200
        assert "weighted_gap_score" in r.json()["data"]


class TestRoadmapsMeEndpoints:

    def _tok(self, c: TestClient) -> str:
        e = f"r{uuid.uuid4().hex[:6]}@x.com"
        c.post("/api/v1/auth/register", json={"email": e, "password": "P@ss123!", "full_name": "T"})
        return c.post("/api/v1/auth/login", data={"username": e, "password": "P@ss123!"}).json()["access_token"]

    def test_list_unauth_401(self, client: TestClient):
        assert client.get("/api/v1/roadmaps/me").status_code == 401

    def test_create_unauth_401(self, client: TestClient):
        assert client.post("/api/v1/roadmaps/me").status_code == 401

    def test_list_empty(self, client: TestClient):
        t = self._tok(client)
        r = client.get("/api/v1/roadmaps/me", headers={"Authorization": f"Bearer {t}"})
        assert r.status_code == 200
        assert r.json()["data"]["total"] == 0

    def test_no_role_400(self, client: TestClient):
        t = self._tok(client)
        assert client.post("/api/v1/roadmaps/me", headers={"Authorization": f"Bearer {t}"}).status_code == 400
