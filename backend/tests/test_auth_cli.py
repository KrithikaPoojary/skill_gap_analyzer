"""Unit and subprocess tests for auth_cli.py."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

_CLI_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "auth_cli.py"


def _parse_json(text: str):
    """Safely extract JSON object or array from stdout."""
    start_candidates = [i for i in (text.find("{"), text.find("[")) if i != -1]
    end_candidates = [i for i in (text.rfind("}"), text.rfind("]")) if i != -1]
    if not start_candidates or not end_candidates:
        raise ValueError(f"No JSON found in: {text!r}")
    start = min(start_candidates)
    end = max(end_candidates)
    return json.loads(text[start : end + 1])


class TestAuthCLI:
    """Test suite for auth_cli.py CLI utility."""

    def test_cli_register_and_login_json(self):
        email = f"cli_user_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword123!"

        # 1. Register user
        reg_cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--json",
            "register",
            "--email",
            email,
            "--password",
            password,
            "--name",
            "CLI Tester",
        ]
        res = subprocess.run(reg_cmd, capture_output=True, text=True, check=True)
        reg_data = _parse_json(res.stdout)
        assert reg_data["status"] == "success"
        assert reg_data["email"] == email
        assert reg_data["full_name"] == "CLI Tester"
        assert "user_id" in reg_data

        # 2. Login
        login_cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--json",
            "login",
            "--email",
            email,
            "--password",
            password,
        ]
        res = subprocess.run(login_cmd, capture_output=True, text=True, check=True)
        login_data = _parse_json(res.stdout)
        assert login_data["status"] == "success"
        assert "access_token" in login_data
        token = login_data["access_token"]

        # 3. Verify token
        vt_cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--json",
            "verify-token",
            "--token",
            token,
        ]
        res = subprocess.run(vt_cmd, capture_output=True, text=True, check=True)
        vt_data = _parse_json(res.stdout)
        assert vt_data["status"] == "valid"
        assert str(vt_data["payload"]["sub"]) == str(reg_data["user_id"])

    def test_cli_login_invalid_credentials_returns_error(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--json",
            "login",
            "--email",
            f"nonexistent_{uuid.uuid4().hex[:8]}@example.com",
            "--password",
            "WrongPassword123!",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode != 0
        data = _parse_json(res.stdout)
        assert data["status"] == "error"

    def test_cli_list_users_json(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--json",
            "list-users",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = _parse_json(res.stdout)
        assert isinstance(data, list)
