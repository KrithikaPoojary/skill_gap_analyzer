"""Unit tests for gap_report_cli.py."""

import json
import subprocess
import sys
from pathlib import Path

_CLI_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "gap_report_cli.py"


class TestGapReportCLI:
    def test_cli_explicit_skills_json(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--skills",
            "Python, FastAPI, Docker",
            "--role",
            "Backend Developer",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        assert data["role_name"] == "Backend Developer"
        assert set(data["matched_skills"]) == {"Python", "FastAPI", "Docker"}
        assert data["gap_score"] > 0.0

    def test_cli_text_extraction_json(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--text",
            "Proficient in Python and Pandas data processing.",
            "--role",
            "Data Scientist",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        assert data["role_name"] == "Data Scientist"
        assert "Python" in data["matched_skills"]
        assert "Pandas" in data["matched_skills"]

    def test_cli_formatted_output(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--skills",
            "React, TypeScript, CSS",
            "--role",
            "Frontend Developer",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = res.stdout
        assert "SKILL GAP ANALYSIS" in out
        assert "Matched Skills" in out
        assert "Missing Skills" in out

    def test_cli_help(self):
        cmd = [sys.executable, str(_CLI_SCRIPT), "--help"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        assert "--skills" in res.stdout
        assert "--role" in res.stdout
