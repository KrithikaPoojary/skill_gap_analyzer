#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Day 1 End-to-End Verification Script
=====================================
Runs a quick smoke-test sequence to confirm the Day 1 setup is fully working:

  1. Import and instantiate application settings.
  2. Start the FastAPI app via TestClient.
  3. Hit GET /api/v1/health and assert HTTP 200 + correct payload.
  4. Confirm OpenAPI schema is available at /openapi.json.
  5. Print a formatted Day 1 summary report.

Usage (from the backend/ directory):
    python scripts/verify_day1.py
"""
import io
import os
import sys

# Ensure the backend/ directory is on sys.path so 'app' package is importable
# when this script is executed from backend/scripts/
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from datetime import datetime

from starlette.testclient import TestClient

# ── Guard against import errors ──────────────────────────────────────────────
try:
    from app.core.config import settings
    from app.main import app
except ImportError as exc:
    print(f"\n❌  Import failed: {exc}")
    print("    Make sure you are running from the backend/ directory")
    print("    with the virtual environment activated.\n")
    sys.exit(1)

SEPARATOR = "─" * 60


def check(label: str, condition: bool) -> bool:
    """Print a pass/fail line and return the condition result."""
    icon = "[PASS]" if condition else "[FAIL]"
    print(f"  {icon}  {label}")
    return condition


def main() -> None:
    print(f"\n{SEPARATOR}")
    print("  Job Market Intelligence & Skill Gap Analyzer")
    print("  Day 1 — End-to-End Verification")
    print(SEPARATOR)

    failures = 0

    # ── 1. Settings ───────────────────────────────────────────────────────────
    print("\n[1/4] Application Settings")
    failures += not check("Settings object is importable", settings is not None)
    failures += not check("app_name is populated", bool(settings.app_name))
    failures += not check("environment == 'development'", settings.environment == "development")
    failures += not check("api_v1_prefix starts with /api/", settings.api_v1_prefix.startswith("/api/"))

    # ── 2. Health endpoint ────────────────────────────────────────────────────
    print("\n[2/4] Health Endpoint  GET /api/v1/health")
    with TestClient(app=app, base_url="http://testserver") as client:
        response = client.get("/api/v1/health")
        body = response.json()

        failures += not check("HTTP 200 OK", response.status_code == 200)
        failures += not check("status == 'healthy'", body.get("status") == "healthy")
        failures += not check("app_name present", "app_name" in body)
        failures += not check("version present", "version" in body)
        failures += not check("timestamp present", "timestamp" in body)

        # Validate ISO 8601 timestamp
        try:
            datetime.fromisoformat(body["timestamp"])
            ts_valid = True
        except (ValueError, KeyError):
            ts_valid = False
        failures += not check("timestamp is valid ISO 8601", ts_valid)

        # ── 3. OpenAPI schema ─────────────────────────────────────────────────
        print("\n[3/4] OpenAPI Schema  GET /openapi.json")
        schema_resp = client.get("/openapi.json")
        failures += not check("HTTP 200 OK", schema_resp.status_code == 200)
        schema = schema_resp.json()
        failures += not check("/api/v1/health path in schema", "/api/v1/health" in schema.get("paths", {}))

        # ── 4. Swagger UI ─────────────────────────────────────────────────────
        print("\n[4/4] Swagger UI  GET /docs")
        docs_resp = client.get("/docs")
        failures += not check("HTTP 200 OK", docs_resp.status_code == 200)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{SEPARATOR}")
    if failures == 0:
        print("  *** ALL CHECKS PASSED - Day 1 setup is verified and working! ***")
    else:
        print(f"  *** {failures} check(s) FAILED - review the output above. ***")
    print(SEPARATOR)
    print(f"\n  App Name  : {settings.app_name}")
    print(f"  Version   : {settings.app_version}")
    print(f"  Env       : {settings.environment}")
    print(f"  API Prefix: {settings.api_v1_prefix}")
    print(f"  DB URL    : {settings.database_url}")
    print(f"\n  Next step : uvicorn app.main:app --reload")
    print(f"              then visit http://localhost:8000/docs\n")

    sys.exit(failures)


if __name__ == "__main__":
    main()
