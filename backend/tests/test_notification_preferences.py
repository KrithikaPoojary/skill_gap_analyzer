"""Tests for notification preferences endpoint."""

from __future__ import annotations
import uuid
from starlette.testclient import TestClient


class TestNotificationPreferencesEndpoint:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        email = f"notifpref_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/notifications/preferences")
        assert resp.status_code == 401

    def test_get_and_patch_preferences(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Initial get has defaults
        resp = client.get("/api/v1/notifications/preferences", headers=headers)
        assert resp.status_code == 200
        prefs = resp.json()
        assert prefs["email_alerts"] is True
        assert prefs["job_matches"] is True

        # Update email_alerts to False
        patch_resp = client.patch(
            "/api/v1/notifications/preferences",
            json={"email_alerts": False, "weekly_digest": False},
            headers=headers,
        )
        assert patch_resp.status_code == 200
        updated = patch_resp.json()
        assert updated["email_alerts"] is False
        assert updated["weekly_digest"] is False
        assert updated["job_matches"] is True

        # Re-fetch confirms persistence
        get2 = client.get("/api/v1/notifications/preferences", headers=headers)
        assert get2.status_code == 200
        assert get2.json()["email_alerts"] is False
        assert get2.json()["weekly_digest"] is False
