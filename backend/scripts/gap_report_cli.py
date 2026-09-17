#!/usr/bin/env python
"""gap_report_cli.py — Interactive CLI demo for Skill Gap Analysis & Role Fit.

Usage examples:
--------------
# Analyse skills from comma-separated list
python scripts/gap_report_cli.py --skills "Python, FastAPI, Docker" --role "Backend Developer"

# Extract skills from resume text then run gap analysis
python scripts/gap_report_cli.py --text "Senior engineer proficient in Python and React." --role "Full Stack Developer"

# Output raw JSON
python scripts/gap_report_cli.py --skills "Python, Docker" --role "Cloud Engineer" --json

# Pipe text from stdin
echo "Skilled in Python, Kubernetes, and PostgreSQL." | python scripts/gap_report_cli.py --role "Platform Engineer"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the backend package root is importable regardless of cwd
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Force UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.services.skill_extractor import skill_extractor  # noqa: E402
from app.services.skill_gap_analyzer import SkillWeight, skill_gap_analyzer  # noqa: E402

# Fallback benchmark taxonomy for standalone CLI mode (no DB required)
DEFAULT_ROLE_BENCHMARKS: dict[str, list[SkillWeight]] = {
    "backend developer": [
        SkillWeight("Python", 1.0),
        SkillWeight("FastAPI", 0.9),
        SkillWeight("PostgreSQL", 0.9),
        SkillWeight("Docker", 0.8),
        SkillWeight("Redis", 0.7),
        SkillWeight("Git", 0.6),
    ],
    "frontend developer": [
        SkillWeight("JavaScript", 1.0),
        SkillWeight("TypeScript", 0.9),
        SkillWeight("React", 1.0),
        SkillWeight("HTML", 0.8),
        SkillWeight("CSS", 0.8),
        SkillWeight("Git", 0.6),
    ],
    "full stack developer": [
        SkillWeight("Python", 1.0),
        SkillWeight("JavaScript", 0.9),
        SkillWeight("React", 0.9),
        SkillWeight("PostgreSQL", 0.8),
        SkillWeight("Docker", 0.7),
        SkillWeight("Git", 0.6),
    ],
    "data scientist": [
        SkillWeight("Python", 1.0),
        SkillWeight("Pandas", 0.9),
        SkillWeight("NumPy", 0.8),
        SkillWeight("Scikit-learn", 0.9),
        SkillWeight("PyTorch", 0.8),
        SkillWeight("SQL", 0.7),
    ],
    "cloud engineer": [
        SkillWeight("AWS", 1.0),
        SkillWeight("Docker", 0.9),
        SkillWeight("Kubernetes", 0.9),
        SkillWeight("Terraform", 0.8),
        SkillWeight("Linux", 0.8),
        SkillWeight("Python", 0.7),
    ],
}

_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_DIM = "\033[2m"


def _colour(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{code}{text}{_RESET}"


def resolve_role_benchmarks(role_name: str) -> tuple[str, list[SkillWeight]]:
    clean = role_name.strip().lower()
    for key, weights in DEFAULT_ROLE_BENCHMARKS.items():
        if clean in key or key in clean:
            return key.title(), weights
    # If custom role, provide default common skills
    return role_name.strip(), [
        SkillWeight("Python", 1.0),
        SkillWeight("Git", 0.7),
        SkillWeight("SQL", 0.8),
    ]


def run_gap_cli(
    *,
    skills: list[str] | None = None,
    text: str | None = None,
    role_name: str = "Backend Developer",
    as_json: bool = False,
) -> int:
    extracted_names: list[str] = []
    if text:
        extracted = skill_extractor.extract_skills(text, min_confidence=0.55)
        extracted_names = [s.name for s in extracted]

    combined_skills = list(set((skills or []) + extracted_names))

    canonical_role, benchmarks = resolve_role_benchmarks(role_name)
    report = skill_gap_analyzer.analyse(
        profile_skills=combined_skills,
        required_skills=benchmarks,
        role_name=canonical_role,
    )

    data = report.to_dict()
    if text:
        data["extracted_from_text"] = extracted_names

    if as_json:
        print(json.dumps(data, indent=2))
        return 0

    # Formatted terminal display
    sep = "=" * 65
    print("\n" + sep)
    print(_colour(f"  SKILL GAP ANALYSIS — {report.role_name.upper()}", _BOLD + _CYAN))
    print(sep)

    score_col = _GREEN if report.weighted_gap_score >= 0.7 else (_YELLOW if report.weighted_gap_score >= 0.4 else _RED)
    print(f"  Weighted Match Score : {_colour(f'{report.weighted_gap_score * 100:.1f}%', _BOLD + score_col)}")
    print(f"  Skill Coverage       : {_colour(f'{report.coverage_pct:.1f}%', _BOLD)} ({len(report.matched_skills)}/{len(benchmarks)} skills)")

    if text:
        print(f"  Extracted from Text  : {', '.join(extracted_names) if extracted_names else '(none)'}")
    print("-" * 65)

    # Matched skills
    matched_str = ", ".join(report.matched_skills) if report.matched_skills else "(none)"
    print(f"  {_colour('[+] Matched Skills', _GREEN)} : {matched_str}")

    # Missing skills
    print(f"  {_colour('[-] Missing Skills', _YELLOW)} :")
    if report.missing_skills:
        for ms in report.missing_skills:
            badge = _colour("[CRITICAL]", _RED + _BOLD) if ms.weight > 0.8 else _colour("[OPTIONAL]", _DIM)
            print(f"      - {ms.name:<18} (weight: {ms.weight:.2f}) {badge}")
    else:
        print("      (none - 100% matched!)")

    # Surplus skills
    if report.surplus_skills:
        print(f"  {_colour('[*] Surplus Skills', _CYAN)} : {', '.join(report.surplus_skills)}")

    print(sep + "\n")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive CLI demo for Skill Gap Analysis against target career benchmarks."
    )
    parser.add_argument(
        "--skills", "-s",
        metavar="LIST",
        type=str,
        help="Comma-separated list of candidate skills (e.g. 'Python, React, Docker').",
    )
    parser.add_argument(
        "--text", "-t",
        metavar="TEXT",
        type=str,
        help="Unstructured resume or profile text to auto-extract skills from.",
    )
    parser.add_argument(
        "--role", "-r",
        metavar="ROLE",
        type=str,
        default="Backend Developer",
        help="Target career role (e.g. 'Backend Developer', 'Data Scientist', 'Cloud Engineer').",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted report.",
    )

    args = parser.parse_args()

    skills_list: list[str] = []
    if args.skills:
        skills_list = [s.strip() for s in args.skills.split(",") if s.strip()]

    text_input = args.text
    if not args.skills and not text_input and not sys.stdin.isatty():
        text_input = sys.stdin.read()

    if not skills_list and not text_input:
        parser.print_help()
        sys.exit(0)

    code = run_gap_cli(
        skills=skills_list,
        text=text_input,
        role_name=args.role,
        as_json=args.json,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
