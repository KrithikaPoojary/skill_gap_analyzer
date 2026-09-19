#!/usr/bin/env python
"""parse_resume_cli.py — Interactive CLI demo for Resume Parsing & Section Segmentation.

Usage examples:
--------------
# Parse a local resume file (PDF, DOCX, TXT)
python scripts/parse_resume_cli.py --file sample_resume.txt

# Parse resume and evaluate match against a target role
python scripts/parse_resume_cli.py --file resume.pdf --role "Backend Developer"

# Parse raw text passed via command-line argument
python scripts/parse_resume_cli.py --text "John Doe\\njohn@example.com\\nSkills: Python, Docker, SQL"

# Output raw structured JSON
python scripts/parse_resume_cli.py --file resume.docx --role "Frontend Developer" --json
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

from app.services.document_parser import document_parser  # noqa: E402
from app.services.resume_segmenter import resume_segmenter  # noqa: E402
from app.services.skill_extractor import skill_extractor  # noqa: E402
from app.services.skill_gap_analyzer import SkillWeight, skill_gap_analyzer  # noqa: E402

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
        SkillWeight("JavaScript", 1.0),
        SkillWeight("React", 0.9),
        SkillWeight("PostgreSQL", 0.9),
        SkillWeight("Docker", 0.8),
        SkillWeight("Git", 0.7),
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
        SkillWeight("NumPy", 0.8),
        SkillWeight("Scikit-Learn", 0.9),
        SkillWeight("Machine Learning", 0.9),
    ],
}


def _get_benchmark_skills(role: str) -> list[SkillWeight]:
    normalized = role.lower().strip()
    if normalized in DEFAULT_ROLE_BENCHMARKS:
        return DEFAULT_ROLE_BENCHMARKS[normalized]
    for key, weights in DEFAULT_ROLE_BENCHMARKS.items():
        if key in normalized or normalized in key:
            return weights
    return [
        SkillWeight("Python", 1.0),
        SkillWeight("SQL", 0.8),
        SkillWeight("Git", 0.7),
        SkillWeight("Docker", 0.7),
    ]


def parse_resume_to_dict(
    file_path: Path | None = None,
    raw_text: str | None = None,
    role: str | None = None,
) -> dict:
    """Parse resume from file or text and return structured dictionary."""
    if file_path:
        with open(file_path, "rb") as f:
            content = f.read()
        filename = file_path.name
        text = document_parser.parse_bytes(content, filename)
        file_size = len(content)
    elif raw_text:
        text = raw_text
        filename = "direct_text_input"
        file_size = len(raw_text.encode("utf-8"))
    else:
        raise ValueError("Either file_path or raw_text must be provided.")

    segments = resume_segmenter.segment(text)

    # Combine segment skills with full-text NLP extraction
    nlp_skills = skill_extractor.extract_skills(text)
    nlp_skill_names = [s.name for s in nlp_skills]
    all_skills = sorted(list(set(segments.skills_raw + nlp_skill_names)), key=lambda s: s.lower())

    result = {
        "filename": filename,
        "file_size_bytes": file_size,
        "char_count": len(text),
        "contact": {
            "name": segments.contact.name,
            "email": segments.contact.email,
            "phone": segments.contact.phone,
            "linkedin_url": segments.contact.linkedin_url,
            "github_url": segments.contact.github_url,
            "website_url": segments.contact.website_url,
            "location": segments.contact.location,
        },
        "sections_detected": list(segments.sections.keys()),
        "skills_extracted": all_skills,
        "raw_text_preview": text[:500] if len(text) > 500 else text,
    }

    if role:
        benchmark = _get_benchmark_skills(role)
        gap = skill_gap_analyzer.analyse(
            profile_skills=all_skills,
            required_skills=benchmark,
            role_name=role,
        )
        match_score = round(gap.coverage_pct, 1)
        result["role_evaluation"] = {
            "target_role": role,
            "match_score": match_score,
            "matched_skills": gap.matched_skills,
            "missing_skills": [s.name for s in gap.missing_skills],
            "critical_missing": gap.missing_critical,
            "readiness_tier": (
                "READY" if match_score >= 80
                else "NEAR_READY" if match_score >= 50
                else "NEEDS_UPSKILLING"
            ),
        }

    return result


def print_formatted_report(data: dict, preview: bool = False) -> None:
    """Print a visually appealing terminal report."""
    print("=" * 64)
    print("           RESUME PARSER & INGESTION REPORT")
    print("=" * 64)
    print(f"File:         {data['filename']} ({data['file_size_bytes']:,} bytes, {data['char_count']:,} chars)")

    # Contact Info
    c = data["contact"]
    print("\n--- Contact Information ---")
    print(f"  Name:       {c.get('name') or 'Not detected'}")
    print(f"  Email:      {c.get('email') or 'Not detected'}")
    print(f"  Phone:      {c.get('phone') or 'Not detected'}")
    if c.get("linkedin_url"):
        print(f"  LinkedIn:   {c['linkedin_url']}")
    if c.get("github_url"):
        print(f"  GitHub:     {c['github_url']}")
    if c.get("website_url"):
        print(f"  Portfolio:  {c['website_url']}")
    if c.get("location"):
        print(f"  Location:   {c['location']}")

    # Sections Detected
    print("\n--- Sections Detected ---")
    sections = data.get("sections_detected", [])
    if sections:
        print("  " + ", ".join(f"[{s.upper()}]" for s in sections))
    else:
        print("  (No standard section headings detected)")

    # Skills Extracted
    print(f"\n--- Skills Extracted ({len(data['skills_extracted'])}) ---")
    skills = data.get("skills_extracted", [])
    if skills:
        col_width = 20
        cols = 3
        for i in range(0, len(skills), cols):
            row = skills[i : i + cols]
            print("  " + "".join(s.ljust(col_width) for s in row))
    else:
        print("  (No skills extracted)")

    # Role Evaluation
    if "role_evaluation" in data:
        eval_data = data["role_evaluation"]
        print(f"\n--- Target Role Fit: {eval_data['target_role']} ---")
        score = eval_data["match_score"]
        tier = eval_data["readiness_tier"]
        print(f"  Match Score:    {score:.1f}% [{tier}]")
        print(f"  Matched Skills: {', '.join(eval_data['matched_skills']) or 'None'}")
        print(f"  Missing Skills: {', '.join(eval_data['missing_skills']) or 'None'}")
        if eval_data["critical_missing"]:
            print(f"  Critical Gaps:  {', '.join(eval_data['critical_missing'])}")

    if preview:
        print("\n--- Document Text Preview ---")
        print(data["raw_text_preview"])

    print("=" * 64)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive CLI tool to parse resumes and evaluate skills against job roles.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file",
        "-f",
        type=Path,
        help="Path to resume file (.pdf, .docx, .txt, .md).",
    )
    group.add_argument(
        "--text",
        "-t",
        type=str,
        help="Direct resume text to parse.",
    )
    parser.add_argument(
        "--role",
        "-r",
        type=str,
        default=None,
        help="Optional target role title (e.g. 'Backend Developer') to evaluate gap against.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Display text preview of the parsed document.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON instead of human-readable text.",
    )

    args = parser.parse_args()

    if args.file and not args.file.exists():
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        data = parse_resume_to_dict(
            file_path=args.file,
            raw_text=args.text,
            role=args.role,
        )
    except Exception as exc:
        print(f"Error parsing resume: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_formatted_report(data, preview=args.preview)


if __name__ == "__main__":
    main()
