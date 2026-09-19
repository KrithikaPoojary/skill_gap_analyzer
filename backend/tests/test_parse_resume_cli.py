"""Unit and subprocess tests for parse_resume_cli.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_CLI_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "parse_resume_cli.py"

_SAMPLE_RESUME_TEXT = """
Jane Doe
jane.doe@example.com | +1-555-987-6543
https://linkedin.com/in/janedoe | https://github.com/janedoe
San Francisco, CA

SUMMARY
Senior Backend Software Engineer with 6 years building distributed systems in Python and Go.

SKILLS
Programming: Python, Go, SQL, Bash
Frameworks & Tools: FastAPI, Docker, PostgreSQL, Redis, Git, Linux

EXPERIENCE
Lead Engineer | TechCorp (2021 - Present)
- Designed asynchronous microservices with FastAPI and PostgreSQL handling 5M requests/day.
- Containerized workflows using Docker and orchestrated deployments.

EDUCATION
B.S. in Computer Science | UC Berkeley
"""


class TestParseResumeCLI:
    """Test suite for parse_resume_cli.py."""

    def test_cli_text_json_output(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--text",
            _SAMPLE_RESUME_TEXT,
            "--role",
            "Backend Developer",
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        assert data["filename"] == "direct_text_input"
        assert data["char_count"] > 100
        assert data["contact"]["email"] == "jane.doe@example.com"
        assert "janedoe" in (data["contact"]["github_url"] or "")
        assert "experience" in data["sections_detected"]
        assert "skills" in data["sections_detected"]

        # Extracted skills check
        skills_lower = [s.lower() for s in data["skills_extracted"]]
        assert "python" in skills_lower
        assert "docker" in skills_lower
        assert "fastapi" in skills_lower

        # Role evaluation check
        assert "role_evaluation" in data
        assert data["role_evaluation"]["target_role"] == "Backend Developer"
        assert data["role_evaluation"]["match_score"] > 50
        assert data["role_evaluation"]["readiness_tier"] in ("READY", "NEAR_READY", "NEEDS_UPSKILLING")

    def test_cli_formatted_text_output(self):
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--text",
            _SAMPLE_RESUME_TEXT,
            "--role",
            "Backend Developer",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out = res.stdout

        assert "RESUME PARSER & INGESTION REPORT" in out
        assert "jane.doe@example.com" in out
        assert "Contact Information" in out
        assert "Skills Extracted" in out
        assert "Target Role Fit: Backend Developer" in out

    def test_cli_with_file_input(self, tmp_path: Path):
        resume_file = tmp_path / "test_resume.txt"
        resume_file.write_text(_SAMPLE_RESUME_TEXT, encoding="utf-8")

        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--file",
            str(resume_file),
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)

        assert data["filename"] == "test_resume.txt"
        assert data["file_size_bytes"] > 0
        assert data["contact"]["email"] == "jane.doe@example.com"
        assert len(data["skills_extracted"]) > 0

    def test_cli_missing_file_error(self, tmp_path: Path):
        non_existent = tmp_path / "missing.pdf"
        cmd = [
            sys.executable,
            str(_CLI_SCRIPT),
            "--file",
            str(non_existent),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode != 0
        assert "not found" in res.stderr.lower()
