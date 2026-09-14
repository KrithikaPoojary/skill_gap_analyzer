"""Market Intelligence and Skill Gap Analytics CLI Reporter.

Extracts aggregated analytics from the database and renders an executive
ASCII intelligence report covering skill demand, salaries, roles, and remote trends.

Usage:
    python scripts/market_report.py
    python scripts/market_report.py --skills-limit 15
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.db.base import Base
from app.db.session import SessionLocal, engine
import app.models  # noqa: F401
from app.services.analytics_service import analytics_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate IT Job Market Intelligence Report.")
    parser.add_argument(
        "--skills-limit",
        type=int,
        default=10,
        help="Number of top skills to display (default: 10)",
    )
    return parser.parse_args()


def render_report(skills_limit: int = 10) -> int:
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        overview = analytics_service.get_market_overview(db)
        skills_data = analytics_service.get_skills_analysis(db, limit=skills_limit)
        salary_data = analytics_service.get_salary_analysis(db)

        print("\n" + "=" * 70)
        print("  JOB MARKET INTELLIGENCE & SKILL GAP EXECUTIVE REPORT")
        print("=" * 70)
        print(f"  Total Active Job Postings:  {overview.total_active_jobs}")
        print(f"  Unique Skills Tracked:      {overview.total_skills_tracked}")
        print(f"  Overall Remote Work Ratio:  {overview.overall_remote_pct:.1f}%")
        print("=" * 70)

        # 1. Top In-Demand Skills
        print("\n  TOP IN-DEMAND TECHNICAL SKILLS:")
        print("  " + "-" * 66)
        print(f"  {'Skill':<20} {'Category':<15} {'Postings':<10} {'Penetration':<12} {'Mandatory'}")
        print("  " + "-" * 66)
        for s in skills_data["top_skills"]:
            print(
                f"  {s['skill_name']:<20} {s['category']:<15} {s['total_postings']:<10} {s['market_penetration_pct']:>5.1f}%       {s['mandatory_count']}"
            )

        # 2. Role Concentration
        print("\n  ROLE CONCENTRATION & REMOTE SHARE:")
        print("  " + "-" * 66)
        print(f"  {'Role Track':<25} {'Postings':<10} {'Market Share':<15} {'Remote %'}")
        print("  " + "-" * 66)
        for r in overview.top_roles:
            print(
                f"  {r.role_name:<25} {r.total_postings:<10} {r.market_share_pct:>6.1f}%          {r.remote_pct:>5.1f}%"
            )

        # 3. Salary Benchmarks
        print("\n  ANNUAL SALARY BENCHMARKS BY SENIORITY (USD):")
        print("  " + "-" * 66)
        print(f"  {'Seniority':<15} {'P25':<12} {'Median':<12} {'P75':<12} {'Sample'}")
        print("  " + "-" * 66)
        for b in salary_data["by_experience"]:
            stats = b["stats"]
            if stats["count"] > 0:
                p25 = f"${stats['p25']:,.0f}" if stats['p25'] else "N/A"
                med = f"${stats['median']:,.0f}" if stats['median'] else "N/A"
                p75 = f"${stats['p75']:,.0f}" if stats['p75'] else "N/A"
                print(f"  {b['dimension_value'].capitalize():<15} {p25:<12} {med:<12} {p75:<12} {stats['count']}")

        # 4. Top Hiring Hubs
        print("\n  TOP HIRING HUBS:")
        print("  " + "-" * 66)
        print(f"  {'Location':<25} {'Postings':<10} {'Market Share':<15} {'Remote %'}")
        print("  " + "-" * 66)
        for loc in overview.top_locations[:6]:
            print(
                f"  {loc.location_name:<25} {loc.total_postings:<10} {loc.market_share_pct:>6.1f}%          {loc.remote_pct:>5.1f}%"
            )

        print("\n" + "=" * 70 + "\n")
        return 0

    except Exception as exc:
        print(f"Error rendering report: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


def main() -> int:
    args = parse_args()
    return render_report(skills_limit=args.skills_limit)


if __name__ == "__main__":
    sys.exit(main())
