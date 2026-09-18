#!/usr/bin/env python
"""generate_roadmap_cli.py — Interactive CLI demo for Personalized Learning Roadmap Generation.

Usage examples:
--------------
# Generate roadmap from a list of skills to learn
python scripts/generate_roadmap_cli.py --skills "FastAPI, Docker, PostgreSQL" --role "Backend Developer"

# Generate roadmap with custom study hours per week
python scripts/generate_roadmap_cli.py --skills "React, Next.js, TypeScript" --role "Frontend Developer" --hours-per-week 15

# Extract skills from resume, calculate gap, and generate roadmap
python scripts/generate_roadmap_cli.py --text "Python developer with basic SQL knowledge." --role "Backend Developer"

# Output raw JSON
python scripts/generate_roadmap_cli.py --skills "Docker, Kubernetes" --role "DevOps Engineer" --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure backend root is on sys.path
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Force UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.services.roadmap.roadmap_generator import GeneratedRoadmap, roadmap_generator  # noqa: E402
from app.services.skill_extractor import skill_extractor  # noqa: E402
from app.services.skill_gap_analyzer import SkillWeight, skill_gap_analyzer  # noqa: E402

DEFAULT_ROLE_REQUIREMENTS: dict[str, list[SkillWeight]] = {
    "backend developer": [
        SkillWeight("Python", 1.0),
        SkillWeight("FastAPI", 0.9),
        SkillWeight("PostgreSQL", 0.9),
        SkillWeight("Docker", 0.8),
        SkillWeight("Redis", 0.7),
        SkillWeight("Git", 0.6),
    ],
    "frontend developer": [
        SkillWeight("HTML", 0.9),
        SkillWeight("CSS", 0.9),
        SkillWeight("JavaScript", 1.0),
        SkillWeight("TypeScript", 0.9),
        SkillWeight("React", 1.0),
        SkillWeight("Next.js", 0.8),
    ],
    "cloud engineer": [
        SkillWeight("Linux", 0.9),
        SkillWeight("AWS", 1.0),
        SkillWeight("Docker", 0.9),
        SkillWeight("Kubernetes", 0.9),
        SkillWeight("Terraform", 0.8),
        SkillWeight("CI/CD", 0.8),
    ],
    "data scientist": [
        SkillWeight("Python", 1.0),
        SkillWeight("SQL", 0.8),
        SkillWeight("Pandas", 0.9),
        SkillWeight("Scikit-learn", 0.9),
        SkillWeight("PyTorch", 0.8),
    ],
}

_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_BLUE = "\033[34m"
_DIM = "\033[2m"


def _colour(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{code}{text}{_RESET}"


def run_roadmap_cli(
    *,
    skills: list[str] | None = None,
    text: str | None = None,
    role_name: str = "Backend Developer",
    hours_per_week: int = 10,
    as_json: bool = False,
) -> int:
    missing_to_sequence: list[str] = []

    if text:
        extracted = skill_extractor.extract_skills(text, min_confidence=0.55)
        candidate_skills = [s.name for s in extracted]

        # Find benchmark role requirements
        clean_role = role_name.strip().lower()
        matched_weights: list[SkillWeight] = []
        for r_key, r_weights in DEFAULT_ROLE_REQUIREMENTS.items():
            if clean_role in r_key or r_key in clean_role:
                matched_weights = r_weights
                break
        if not matched_weights:
            matched_weights = [
                SkillWeight("Python", 1.0),
                SkillWeight("FastAPI", 0.9),
                SkillWeight("Docker", 0.8),
            ]

        gap_report = skill_gap_analyzer.analyse(
            profile_skills=candidate_skills,
            required_skills=matched_weights,
            role_name=role_name,
        )
        missing_to_sequence = [s.name for s in gap_report.missing_skills]
    elif skills:
        missing_to_sequence = skills
    else:
        missing_to_sequence = ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"]

    roadmap: GeneratedRoadmap = roadmap_generator.generate(
        missing_skills=missing_to_sequence,
        role_title=role_name,
        weekly_commitment_hours=hours_per_week,
    )

    data = roadmap.to_dict()
    if as_json:
        print(json.dumps(data, indent=2))
        return 0

    # Formatted terminal visual display
    sep = "=" * 70
    print("\n" + sep)
    print(_colour(f"  LEARNING ROADMAP — {roadmap.role_title.upper()}", _BOLD + _CYAN))
    print(sep)
    print(
        f"  Total Curriculum      : {_colour(f'{roadmap.total_skills} skills', _BOLD)} "
        f"| {_colour(f'{roadmap.total_estimated_hours} total study hours', _BOLD)}"
    )
    print(
        f"  Pacing & Timeline     : {_colour(f'{roadmap.weekly_commitment_hours} hrs/week', _YELLOW)} "
        f"-> {_colour(f'{roadmap.estimated_weeks} weeks to job readiness', _GREEN + _BOLD)}"
    )
    print("-" * 70)

    for phase in roadmap.phases:
        print(f"\n  {_colour(f'PHASE {phase.phase_number}: {phase.phase_title.upper()}', _BOLD + _BLUE)}")
        print(f"  {_colour(phase.description, _DIM)}")
        print(f"  Target Duration: {phase.estimated_weeks} weeks ({phase.total_phase_hours} study hours)")
        print("  " + "-" * 66)

        print("  Skills & Curricula:")
        for sk in phase.skills:
            diff_badge = (
                _colour("[Easy]", _GREEN)
                if sk.difficulty == "beginner"
                else (_colour("[Medium]", _YELLOW) if sk.difficulty == "intermediate" else _colour("[Hard]", _RED))
            )
            print(f"    * {sk.name:<18} {diff_badge} ({sk.estimated_hours}h) — {_colour(sk.recommended_practice, _DIM)}")
            for res in sk.resources[:1]:
                print(f"        -> {res.get('title')}: {_colour(res.get('url'), _CYAN)}")

        print(f"\n  {_colour('Capstone Milestone Challenge:', _BOLD)}")
        print(f"    * Project : {_colour(phase.capstone_project_title, _BOLD)}")
        print(f"    * Spec    : {phase.capstone_project_description}")
        print("  " + "." * 66)

    print("\n" + sep)
    print(_colour("  Roadmap complete. Consistent practice bridges the gap!", _GREEN + _BOLD))
    print(sep + "\n")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive CLI tool for Personalized Learning Roadmap Generation."
    )
    parser.add_argument(
        "--skills", "-s",
        metavar="LIST",
        type=str,
        help="Comma-separated deficit skills to sequence (e.g. 'Python, FastAPI, Docker').",
    )
    parser.add_argument(
        "--text", "-t",
        metavar="TEXT",
        type=str,
        help="Resume text to extract candidate skills from and compute deficit.",
    )
    parser.add_argument(
        "--role", "-r",
        metavar="ROLE",
        type=str,
        default="Backend Developer",
        help="Target career role (e.g. 'Backend Developer', 'Frontend Developer', 'Cloud Engineer').",
    )
    parser.add_argument(
        "--hours-per-week", "-w",
        metavar="HOURS",
        type=int,
        default=10,
        help="Weekly study commitment in hours (default: 10).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of formatted report.",
    )

    args = parser.parse_args()

    skills_list: list[str] | None = None
    if args.skills:
        skills_list = [s.strip() for s in args.skills.split(",") if s.strip()]

    code = run_roadmap_cli(
        skills=skills_list,
        text=args.text,
        role_name=args.role,
        hours_per_week=args.hours_per_week,
        as_json=args.json,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
