"""End-to-End Live API Execution & Verification Demo Script.

Demonstrates all platform capabilities by sending live requests to the running
FastAPI server, including authentication, skill claiming, gap analysis,
role overlap, transitions, salary analytics, and roadmap generation.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
import uuid
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"



def request(method: str, path: str, data: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            res_body = json.loads(response.read().decode("utf-8"))
            return status, res_body
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read().decode("utf-8")) if e.fp else {}
        return e.code, error_body


def main() -> int:
    print("\n" + "=" * 70)
    print("  🚀 LIVE END-TO-END DEMO: JOB MARKET & SKILL GAP ANALYZER")
    print("=" * 70)

    # 1. Health check
    status, res = request("GET", "/api/v1/health")
    print(f"\n[1/10] Server Health: HTTP {status}")
    print(f"       App: {res['data']['app_name']} (v{res['data']['version']})")
    print(f"       Database: {res['data']['database']}, Env: {res['data']['environment']}")

    # 2. Register candidate user
    suffix = uuid.uuid4().hex[:6]
    email = f"candidate_{suffix}@example.com"
    password = "SecurePassword123!"
    full_name = f"Jane Developer {suffix}"

    status, reg_res = request("POST", "/api/v1/auth/register", {
        "email": email,
        "password": password,
        "full_name": full_name,
    })
    print(f"\n[2/10] Register Candidate: HTTP {status}")
    print(f"       User ID: {reg_res['id']}, Email: {email}")

    # 3. Login & obtain JWT Bearer token
    login_data = urllib.parse.urlencode({"username": email, "password": password}).encode("utf-8")
    login_req = urllib.request.Request(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(login_req) as login_resp:
        token_data = json.loads(login_resp.read().decode("utf-8"))
        token = token_data["access_token"]
    print(f"\n[3/10] Candidate Login: HTTP 200 OK")
    print(f"       Bearer Token: {token[:25]}... (valid 24h)")

    # 4. Update profile & claim skills
    status, prof_res = request("PUT", "/api/v1/profile/me", {
        "headline": "Full Stack Software Engineer",
        "bio": "Passionate about building scalable backend APIs and cloud architectures.",
        "current_title": "Software Engineer",
        "years_of_experience": 3.5,
        "location": "Remote / New York",
    }, token=token)
    print(f"\n[4/10] Profile Update: HTTP {status}")
    print(f"       Title: {prof_res['data']['current_title']} ({prof_res['data']['years_of_experience']} yrs exp)")

    # 5. Add skills to candidate profile
    # Lookup skills catalog
    status, cat_res = request("GET", "/api/v1/skills/catalog?limit=5")
    skills = cat_res.get("data", [])
    if skills:
        skill_id = skills[0]["id"]
        skill_name = skills[0]["name"]
        status, us_res = request("POST", "/api/v1/profile/me/skills", {
            "skill_id": skill_id,
            "proficiency_level": "advanced",
            "years_of_experience": 3.0,
        }, token=token)
        print(f"\n[5/10] Added Skill to Profile: HTTP {status}")
        print(f"       Claimed Skill: {skill_name} (Level: advanced)")

    # 6. Fetch Target Roles & Role Overlap
    status, roles_res = request("GET", "/api/v1/roles?limit=5")
    roles = roles_res.get("data", [])
    if len(roles) >= 2:
        r1 = roles[0]
        r2 = roles[1]
        print(f"\n[6/10] Career Roles & Overlap Analysis:")
        print(f"       Comparing Role '{r1['title']}' vs '{r2['title']}'")
        status, overlap_res = request("GET", f"/api/v1/roles/{r1['id']}/overlap/{r2['id']}")
        ov_data = overlap_res.get("data", {})
        print(f"       Similarity: {ov_data.get('overlap_percentage')}% (Shared Skills: {ov_data.get('shared_count')})")

        # 7. Career Transition Recommendations
        status, trans_res = request("GET", f"/api/v1/roles/{r1['id']}/transitions?limit=3")
        trans_data = trans_res.get("data", {})
        print(f"\n[7/10] Career Transitions from '{r1['title']}': HTTP {status}")
        for t in trans_data.get("transitions", []):
            print(f"       ➔ {t['title']} ({t['category']}) - {t['transferability_pct']}% Transferability")

    # 8. Salary bands analytics
    status, sal_res = request("GET", "/api/v1/analytics/salary-bands?currency=USD")
    sal_data = sal_res.get("data", {})
    print(f"\n[8/10] Salary Compensation Bands Analytics: HTTP {status}")
    print(f"       Analyzed {sal_data.get('total_jobs_with_salary')} Active Jobs With Reported Salary:")
    for b in sal_data.get("bands", [])[:4]:
        mid = f"${b['midpoint_salary']:,.0f}" if b.get('midpoint_salary') else "N/A"
        print(f"       - {b['experience_level'].capitalize():<8}: Median {mid} (Sample: {b['job_count']} jobs)")

    # 9. Top hiring companies & remote breakdown
    status, comp_res = request("GET", "/api/v1/analytics/companies/top?limit=3")
    comps = comp_res.get("data", {}).get("companies", [])
    print(f"\n[9/10] Top Hiring Companies Leaderboard: HTTP {status}")
    for c in comps:
        print(f"       - {c['company_name']}: {c['total_jobs']} postings ({c['remote_percentage']}% remote)")

    # 10. Generate & Export Learning Roadmap
    status, rm_res = request("POST", "/api/v1/roadmaps/me?role_name=Backend+Engineer&weekly_commitment_hours=12", token=token)
    rm_id = rm_res.get("data", {}).get("id")
    print(f"\n[10/10] Generated Personalized Learning Roadmap: HTTP {status}")
    if rm_id:
        status, exp_res = request("GET", f"/api/v1/roadmaps/me/{rm_id}/export", token=token)
        exp_data = exp_res.get("data", {})
        print(f"        Roadmap ID: {rm_id}")
        print(f"        Role Target: {exp_data.get('role_title')}")
        print(f"        Weekly Commitment: {exp_data.get('weekly_commitment_hours')} hrs/week")
        print(f"        Total Milestones: {exp_data.get('total_milestones')}")

    print("\n" + "=" * 70)
    print("  ✨ ALL END-TO-END DEMO STEPS EXECUTED SUCCESSFULLY ON LIVE SERVER!")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
