"""Unit tests for generate_roadmap_cli.py."""

import json
import subprocess
import sys
from pathlib import Path

_CLI_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "generate_roadmap_cli.py"


class TestGenerateRoadmapCLI:
    def test_cli_explicit_skills_json(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--skills",
            "Python, FastAPI, Docker",
            "--role",
            "Backend Developer",
            "--hours-per-week",
            "10",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        assert data["role_title"] == "Backend Developer"
        assert data["total_skills"] == 3
        assert data["total_estimated_hours"] > 0
        assert len(data["phases"]) > 0

    def test_cli_text_extraction_json(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--text",
            "Developer with Python and SQL experience.",
            "--role",
            "Backend Developer",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        assert data["role_title"] == "Backend Developer"
        assert "phases" in data

    def test_cli_formatted_output(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--skills",
            "React, Next.js",
            "--role",
            "Frontend Developer",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = res.stdout
        assert "LEARNING ROADMAP" in out
        assert "PHASE" in out
        assert "Capstone Milestone Challenge" in out

    def test_cli_help(self):
        cmd = [sys.executable, str(_CLI_SCRIPT), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        assert "--skills" in res.stdout
        assert "--hours-per-week" in res.stdout
