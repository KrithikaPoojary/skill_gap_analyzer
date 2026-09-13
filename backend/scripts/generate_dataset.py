"""Script to generate a realistic, diverse dataset of 500+ IT job postings.

Outputs:
- backend/data/jobs_dataset.json
- backend/data/jobs_dataset.csv
"""

from __future__ import annotations

import csv
import json
import os
import random

# Fixed seed for reproducibility
random.seed(42)

COMPANIES = [
    "Stripe", "Datadog", "Snowflake", "Shopify", "Airbnb", "Uber", "Lyft",
    "Coinbase", "Figma", "Canva", "Atlassian", "Twilio", "Elastic", "MongoDB Inc",
    "Cloudflare", "HashiCorp", "Vercel", "GitLab", "GitHub", "Automattic",
    "Acme Technologies", "Apex Systems", "Novasphere Labs", "Synthetix Cloud",
    "Krypton Data", "BluePulse AI", "OmniScale Networks", "Zenith Health Tech",
    "FinEdge Capital", "AeroDynamics Soft", "Hyperion Analytics", "Aegis Security",
    "CodeCraft Studio", "Orbit Software", "Vanguard Digital", "NextWave Mobility",
]

LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
    "Boston, MA", "Chicago, IL", "Denver, CO", "Los Angeles, CA",
    "Bengaluru, India", "Hyderabad, India", "Pune, India",
    "London, UK", "Berlin, Germany", "Toronto, Canada", "Remote",
]

ROLE_TEMPLATES = [
    {
        "role": "Backend Engineer",
        "prefixes": ["Junior", "Mid-Level", "Senior", "Staff", "Lead"],
        "descriptions": [
            "We are seeking an engineer to build resilient, distributed backend services, design robust REST/gRPC APIs, and optimize database access.",
            "Join our core services team building high-throughput microservices handling millions of API requests daily with high availability.",
            "You will architect and maintain scalable server-side systems, collaborate with cross-functional teams, and write clean, tested code.",
        ],
        "core_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "optional_skills": ["Redis", "AWS", "Kafka", "CI/CD", "Linux", "Kubernetes", "Pytest", "REST API", "Microservices"],
        "salary_range": (85000, 185000),
    },
    {
        "role": "Frontend Engineer",
        "prefixes": ["Junior", "Frontend", "Senior", "Lead", "Staff"],
        "descriptions": [
            "Help design and implement interactive, responsive user interfaces that deliver exceptional user experiences.",
            "Develop modern, component-driven web applications using React, TypeScript, and modern CSS architecture.",
            "You will optimize client-side rendering performance, integrate GraphQL/REST endpoints, and build reusable UI components.",
        ],
        "core_skills": ["React", "TypeScript", "JavaScript", "Tailwind CSS", "Git"],
        "optional_skills": ["Next.js", "Vue.js", "Jest", "Cypress", "GraphQL", "REST API", "Agile"],
        "salary_range": (80000, 175000),
    },
    {
        "role": "Full Stack Developer",
        "prefixes": ["Full Stack", "Senior Full Stack", "Lead Full Stack", "Junior Full Stack"],
        "descriptions": [
            "Looking for a full stack engineer comfortable working from React client-side workflows to backend APIs and relational databases.",
            "Drive features end-to-end: UI wireframe to database schema, API routing, and continuous integration pipeline.",
            "Design scalable web systems, implement secure authentication, and optimize full-stack responsiveness.",
        ],
        "core_skills": ["Python", "React", "TypeScript", "PostgreSQL", "Git"],
        "optional_skills": ["FastAPI", "Django", "Node.js", "Docker", "AWS", "Redis", "Tailwind CSS", "REST API"],
        "salary_range": (90000, 190000),
    },
    {
        "role": "DevOps & Cloud Engineer",
        "prefixes": ["DevOps", "Senior DevOps", "Cloud Infrastructure", "Site Reliability", "Lead SRE"],
        "descriptions": [
            "Build automated CI/CD deployment pipelines, manage Kubernetes infrastructure, and enforce cloud security posture.",
            "Ensure system reliability, low latency, and zero-downtime upgrades across multi-region cloud environments.",
            "Maintain infrastructure as code with Terraform, containerize services with Docker, and configure Prometheus/Grafana monitoring.",
        ],
        "core_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux"],
        "optional_skills": ["GCP", "Azure", "CI/CD", "Ansible", "Python", "Bash", "Prometheus", "Git"],
        "salary_range": (95000, 205000),
    },
    {
        "role": "Data Engineer",
        "prefixes": ["Data", "Senior Data", "Lead Data", "Staff Data"],
        "descriptions": [
            "Design, construct, and manage scalable data pipelines, ETL workflows, and lakehouse storage layers.",
            "Optimize streaming and batch data architectures for downstream analytics, dashboards, and ML models.",
            "Build reliable data pipelines, write SQL queries, and manage distributed data storage platforms.",
        ],
        "core_skills": ["Python", "SQL", "PostgreSQL", "Kafka", "Docker"],
        "optional_skills": ["Snowflake", "AWS", "Pandas", "Linux", "Git", "Redis", "Elasticsearch"],
        "salary_range": (95000, 195000),
    },
    {
        "role": "Machine Learning Engineer",
        "prefixes": ["Applied ML", "Senior Machine Learning", "AI/ML", "Lead Machine Learning"],
        "descriptions": [
            "Train, evaluate, and deploy production machine learning models and LLM agent workflows at scale.",
            "Bridge research and production: transform experimental prototypes into low-latency inference APIs.",
            "Work with deep neural networks, model fine-tuning, embeddings, and real-time inference serving.",
        ],
        "core_skills": ["Python", "Machine Learning", "PyTorch", "Pandas", "Scikit-Learn"],
        "optional_skills": ["TensorFlow", "FastAPI", "Docker", "AWS", "NLP", "LangChain", "Git"],
        "salary_range": (110000, 225000),
    },
    {
        "role": "QA Automation Engineer",
        "prefixes": ["QA", "Senior QA Automation", "Software Test", "Lead SDET"],
        "descriptions": [
            "Design, write, and execute automated regression test suites for microservices and modern web frontends.",
            "Partner with development teams to incorporate automated tests into CI/CD pipelines and drive test coverage.",
            "Ensure platform reliability through end-to-end integration, API contracts, and browser automation suites.",
        ],
        "core_skills": ["Python", "Pytest", "Selenium", "Git", "CI/CD"],
        "optional_skills": ["Cypress", "Jest", "Docker", "REST API", "Linux", "Bash"],
        "salary_range": (75000, 155000),
    },
]

EXPERIENCE_LEVELS = ["entry", "mid", "senior", "lead"]
EMPLOYMENT_TYPES = ["full_time", "full_time", "full_time", "contract", "internship"]
PLATFORMS = ["linkedin", "indeed", "glassdoor", "naukri", "synthetic"]


def generate_postings(total_count: int = 520) -> list[dict]:
    postings = []
    seen_keys = set()

    while len(postings) < total_count:
        template = random.choice(ROLE_TEMPLATES)
        prefix = random.choice(template["prefixes"])
        title = f"{prefix} {template['role']}" if prefix != template["role"] else template["role"]

        company = random.choice(COMPANIES)
        loc = random.choice(LOCATIONS)
        is_remote = loc == "Remote" or random.random() < 0.35

        dedup_key = (title.lower(), company.lower(), loc.lower())
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        # Seniority deduction
        if "Junior" in prefix or "Intern" in prefix:
            exp_level = "entry"
        elif "Senior" in prefix:
            exp_level = "senior"
        elif "Lead" in prefix or "Staff" in prefix:
            exp_level = "lead"
        else:
            exp_level = random.choice(["mid", "mid", "senior"])

        # Salary calculation
        base_min, base_max = template["salary_range"]
        mult = 0.8 if exp_level == "entry" else (1.0 if exp_level == "mid" else (1.3 if exp_level == "senior" else 1.55))
        min_salary = round(base_min * mult, -3)
        max_salary = round(base_max * mult, -3)

        # Select skills
        required_skills = list(template["core_skills"])
        # Add 2-4 optional skills
        optional_sample = random.sample(template["optional_skills"], k=random.randint(2, min(4, len(template["optional_skills"]))))

        skill_records = []
        for s in required_skills:
            skill_records.append({
                "name": s,
                "is_required": True,
                "importance_weight": round(random.uniform(1.2, 2.0), 1),
            })
        for s in optional_sample:
            skill_records.append({
                "name": s,
                "is_required": False,
                "importance_weight": round(random.uniform(0.8, 1.2), 1),
            })

        desc = random.choice(template["descriptions"])
        req_raw = "\n".join(f"- Proficient in {s['name']}" for s in skill_records if s["is_required"])

        item = {
            "title": title,
            "company_name": company,
            "location": loc,
            "is_remote": is_remote,
            "employment_type": random.choice(EMPLOYMENT_TYPES),
            "experience_level": exp_level,
            "min_salary": min_salary,
            "max_salary": max_salary,
            "salary_currency": "USD",
            "description": desc,
            "requirements_raw": req_raw,
            "source_url": f"https://jobs.example.com/{company.lower().replace(' ', '')}/{len(postings) + 1}",
            "source_platform": random.choice(PLATFORMS),
            "is_active": True,
            "skills": skill_records,
        }
        postings.append(item)

    return postings


def main() -> None:
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(backend_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    postings = generate_postings(520)

    # 1. Save JSON
    json_path = os.path.join(data_dir, "jobs_dataset.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(postings, f, indent=2)
    print(f"Saved {len(postings)} jobs to {json_path}")

    # 2. Save CSV
    csv_path = os.path.join(data_dir, "jobs_dataset.csv")
    fields = [
        "title", "company_name", "location", "is_remote", "employment_type",
        "experience_level", "min_salary", "max_salary", "salary_currency",
        "description", "requirements_raw", "source_url", "source_platform",
        "skills_str",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for p in postings:
            row = {k: p[k] for k in fields if k != "skills_str"}
            # Comma-separated list of skill names
            row["skills_str"] = ",".join(s["name"] for s in p["skills"])
            writer.writerow(row)
    print(f"Saved {len(postings)} jobs to {csv_path}")


if __name__ == "__main__":
    main()
