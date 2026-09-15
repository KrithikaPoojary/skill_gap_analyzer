#!/usr/bin/env python
"""extract_skills_cli.py — Interactive CLI demo for the Skill Extraction Engine.

Usage examples
--------------
# Extract from inline text
python scripts/extract_skills_cli.py --text "Senior Python developer with FastAPI and AWS."

# Extract from a file
python scripts/extract_skills_cli.py --file path/to/job_description.txt

# Use a higher confidence threshold
python scripts/extract_skills_cli.py --text "..." --min-confidence 0.7

# Pipe stdin
echo "Kubernetes and Terraform experience required." | python scripts/extract_skills_cli.py

# Batch mode: process every .txt file in a directory
python scripts/extract_skills_cli.py --batch-dir path/to/jd_folder/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ensure the backend package root is importable regardless of cwd
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.services.extractor.batch_extractor import batch_skill_extractor  # noqa: E402
from app.services.skill_extractor import skill_extractor  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Formatting helpers
# ─────────────────────────────────────────────────────────────────────────────

_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_DIM = "\033[2m"


def _colour(text: str, code: str) -> str:
    """Wrap text in ANSI colour codes (skipped when stdout is not a TTY)."""
    if not sys.stdout.isatty():
        return text
    return f"{code}{text}{_RESET}"


def _header(title: str) -> None:
    width = 62
    print(_colour("═" * width, _CYAN))
    print(_colour(f"  {title}", _BOLD + _CYAN))
    print(_colour("═" * width, _CYAN))


def _confidence_bar(score: float, width: int = 20) -> str:
    filled = round(score * width)
    bar = "█" * filled + "░" * (width - filled)
    if score >= 0.75:
        colour = _GREEN
    elif score >= 0.50:
        colour = _YELLOW
    else:
        colour = _RED
    return _colour(f"[{bar}]", colour) + f" {score:.2f}"


def _print_results(results: list, elapsed_ms: float, source_label: str = "") -> None:
    if source_label:
        print(_colour(f"\n  Source: {source_label}", _DIM))

    if not results:
        print(_colour("  ⚠  No skills extracted from the provided text.", _YELLOW))
        return

    print(f"\n  {'#':<4} {'Skill':<28} {'Conf':<28} {'Freq'}")
    print(_colour("  " + "─" * 58, _DIM))

    for i, skill in enumerate(results, start=1):
        bar = _confidence_bar(skill.confidence)
        variants = ", ".join(skill.matched_variants) if len(skill.matched_variants) > 1 else ""
        alias_note = _colour(f"  ↳ aliases: {variants}", _DIM) if variants else ""
        print(f"  {i:<4} {skill.name:<28} {bar}  ×{skill.occurrences}")
        if alias_note:
            print(alias_note)
        if skill.context_snippets:
            snippet = skill.context_snippets[0][:70].strip()
            print(_colour(f"       \"{snippet}…\"", _DIM))

    print()
    print(_colour(f"  ✔  {len(results)} skill(s) extracted in {elapsed_ms:.1f} ms", _GREEN))


# ─────────────────────────────────────────────────────────────────────────────
# Single-document extraction
# ─────────────────────────────────────────────────────────────────────────────

def run_single(text: str, min_confidence: float, source_label: str = "") -> None:
    _header("Skill Gap Analyzer — Extraction Engine")
    start = time.perf_counter()
    results = skill_extractor.extract_skills(text, min_confidence=min_confidence)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    _print_results(results, elapsed_ms, source_label)


# ─────────────────────────────────────────────────────────────────────────────
# Batch-directory extraction
# ─────────────────────────────────────────────────────────────────────────────

def run_batch(batch_dir: Path, min_confidence: float) -> None:
    txt_files = sorted(batch_dir.glob("*.txt"))
    if not txt_files:
        print(_colour(f"  No .txt files found in: {batch_dir}", _RED))
        sys.exit(1)

    docs: list[tuple[str, str]] = []
    for fp in txt_files:
        try:
            docs.append((fp.name, fp.read_text(encoding="utf-8")))
        except OSError as exc:
            print(_colour(f"  ⚠  Skipping {fp.name}: {exc}", _YELLOW))

    _header(f"Skill Gap Analyzer — Batch Extraction ({len(docs)} documents)")
    report = batch_skill_extractor.extract_batch(docs, min_confidence=min_confidence)

    print(f"\n  Documents processed : {report.total_documents}")
    print(f"  Total skills found  : {report.total_skills_extracted}")
    print(f"  Avg skills / doc    : {report.avg_skills_per_document:.1f}")
    print(f"  Total duration      : {report.total_duration_ms:.1f} ms")

    if report.skill_frequency:
        print(_colour("\n  Top 10 skills across corpus:", _BOLD))
        top10 = sorted(report.skill_frequency.items(), key=lambda kv: kv[1], reverse=True)[:10]
        for rank, (name, freq) in enumerate(top10, start=1):
            bar = _confidence_bar(min(freq / top10[0][1], 1.0), width=16)
            print(f"    {rank:>2}. {name:<25} {bar}  (mentioned in {freq} doc(s))")

    print(_colour("\n  Per-document summary:", _BOLD))
    for dr in report.document_results:
        status = _colour(f"{dr.total_skills} skills", _GREEN if dr.total_skills > 0 else _YELLOW)
        print(f"    {dr.doc_id:<35} → {status}")

    print()


# ─────────────────────────────────────────────────────────────────────────────
# JSON output mode
# ─────────────────────────────────────────────────────────────────────────────

def run_json(text: str, min_confidence: float) -> None:
    results = skill_extractor.extract_skills(text, min_confidence=min_confidence)
    print(json.dumps([s.to_dict() for s in results], indent=2))


# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_skills_cli",
        description="Skill Extraction Engine — CLI Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--text", "-t",
        metavar="TEXT",
        help="Inline text to extract skills from.",
    )
    source_group.add_argument(
        "--file", "-f",
        metavar="PATH",
        type=Path,
        help="Path to a .txt file to extract skills from.",
    )
    source_group.add_argument(
        "--batch-dir", "-b",
        metavar="DIR",
        type=Path,
        help="Directory containing .txt files for batch extraction.",
    )
    parser.add_argument(
        "--min-confidence", "-c",
        metavar="FLOAT",
        type=float,
        default=0.0,
        help="Minimum confidence threshold (0.0–1.0). Default: 0.0",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of the formatted table.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Validate confidence range
    if not (0.0 <= args.min_confidence <= 1.0):
        parser.error("--min-confidence must be between 0.0 and 1.0")

    # ── batch-dir mode
    if args.batch_dir:
        if not args.batch_dir.is_dir():
            parser.error(f"--batch-dir '{args.batch_dir}' is not a valid directory.")
        run_batch(args.batch_dir, args.min_confidence)
        return

    # ── Resolve text input
    if args.file:
        if not args.file.exists():
            parser.error(f"File not found: {args.file}")
        text = args.file.read_text(encoding="utf-8")
        source_label = str(args.file)
    elif args.text:
        text = args.text
        source_label = "<inline>"
    elif not sys.stdin.isatty():
        # stdin pipe
        text = sys.stdin.read()
        source_label = "<stdin>"
    else:
        parser.print_help()
        sys.exit(0)

    if args.json:
        run_json(text, args.min_confidence)
    else:
        run_single(text, args.min_confidence, source_label=source_label)


if __name__ == "__main__":
    main()
