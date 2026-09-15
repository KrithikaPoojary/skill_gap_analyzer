"""Smoke tests for the extract_skills_cli.py command-line tool.

Verifies that the CLI can be invoked as a subprocess and produces valid output
for both normal text input and the --json output mode.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_CLI = Path(__file__).resolve().parent.parent / "scripts" / "extract_skills_cli.py"


class TestExtractSkillsCLI:
    """Smoke tests: invoke the CLI as a child process and validate its output."""

    def _run(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(_CLI), *args]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            input=stdin,
        )

    def test_cli_runs_with_text_flag(self) -> None:
        result = self._run("--text", "Python and Docker engineer wanted.")
        assert result.returncode == 0, result.stderr
        assert "Python" in result.stdout or "Docker" in result.stdout

    def test_cli_json_output_is_valid(self) -> None:
        result = self._run(
            "--text", "Hiring a React and TypeScript developer.",
            "--json",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 1
        # Verify schema shape
        first = data[0]
        assert "name" in first
        assert "confidence" in first
        assert "occurrences" in first

    def test_cli_min_confidence_filters_results(self) -> None:
        result = self._run(
            "--text", "Python, AWS, Haskell, Erlang, Prolog experience.",
            "--json",
            "--min-confidence", "0.8",
        )
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        for skill in data:
            assert skill["confidence"] >= 0.8, (
                f"Skill '{skill['name']}' has confidence {skill['confidence']} < 0.8"
            )

    def test_cli_stdin_pipe_mode(self) -> None:
        result = self._run(stdin="Kubernetes and Terraform DevOps engineer.")
        assert result.returncode == 0, result.stderr
        # Should produce formatted output without error
        assert len(result.stdout) > 0

    def test_cli_empty_text_exits_cleanly(self) -> None:
        result = self._run("--text", "   ")
        assert result.returncode == 0, result.stderr

    def test_cli_file_not_found_exits_with_error(self) -> None:
        result = self._run("--file", "nonexistent_file_xyzzy.txt")
        assert result.returncode != 0

    def test_cli_invalid_confidence_exits_with_error(self) -> None:
        result = self._run("--text", "Python dev", "--min-confidence", "5.0")
        assert result.returncode != 0
