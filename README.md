# Job Market Intelligence & Skill Gap Analyzer

An end-to-end platform that analyzes IT job market data and a candidate's skill profile to surface job matches, skill gaps, salary trends, and a personalized learning roadmap.

---

## Prerequisites

- Python 3.10 or higher
- Git

---

## Setup & Run

```bash
# 1. Clone the repository
git clone https://github.com/KrithikaPoojary/skill_gap_analyzer.git
cd skill_gap_analyzer

# 2. Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Copy environment config
cp .env.example .env

# 5. Start the development server
python main.py
```

Server runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

---

## Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Resume Parsing CLI

```bash
# Parse a resume file and evaluate fit against a target role
python scripts/parse_resume_cli.py --file path/to/resume.pdf --role "Backend Developer"
```

---

## Authentication & User Management CLI

```bash
# Register a new user
python scripts/auth_cli.py register --email alice@example.com --password "SecurePass123!" --name "Alice Smith"

# Authenticate and receive a JWT bearer access token
python scripts/auth_cli.py login --email alice@example.com --password "SecurePass123!"

# Verify and inspect JWT token payload
python scripts/auth_cli.py verify-token --token <JWT_ACCESS_TOKEN>

# List all registered users
python scripts/auth_cli.py list-users --json
```

---

## Authenticated Profile & Personalization API

All endpoints require `Authorization: Bearer <token>`:

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/profile/me` | `GET` | Retrieve full candidate profile with skills and target roles |
| `/api/v1/profile/me` | `PUT` | Update headline, bio, experience, location, URLs |
| `/api/v1/profile/me/skills` | `POST` | Claim individual skill with proficiency level |
| `/api/v1/profile/me/skills/bulk` | `POST` | Bulk claim skills |
| `/api/v1/profile/me/skills/{id}` | `DELETE` | Remove skill from profile |
| `/api/v1/profile/me/stats` | `GET` | Aggregated user metrics and profile completeness |
| `/api/v1/resume/upload-to-my-profile` | `POST` | Parse resume & auto-populate candidate profile |
| `/api/v1/gap-analysis/me` | `GET` | Benchmark candidate skills against target role |
| `/api/v1/roadmaps/me` | `POST` | Generate & persist custom learning roadmap |
| `/api/v1/roadmaps/me` | `GET` | List all persisted learning roadmaps |
| `/api/v1/auth/me` | `DELETE` | Deactivate candidate account |
