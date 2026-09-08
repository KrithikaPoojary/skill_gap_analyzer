# Job Market Intelligence & Skill Gap Analyzer

> **An end-to-end platform that analyzes IT job market data and a candidate's skill profile to surface job matches, skill gaps, salary trends, and a personalized learning roadmap.**

---

## Project Status

| Day | Phase | Status |
|-----|-------|--------|
| **Day 1** | Project Planning & Repository Setup | ✅ Complete |
| Day 2 | Backend Foundation & Middleware | 🔜 Upcoming |
| Day 3–5 | Database Design & Data Pipeline | 🔜 Upcoming |
| Day 6–10 | Analytics & Matching Engine | 🔜 Upcoming |
| Day 11–16 | Advanced Recommendations & Market Intelligence | 🔜 Upcoming |
| Day 17–23 | React Frontend & Visualizations | 🔜 Upcoming |
| Day 24–30 | Auth, Docker, Testing & Release | 🔜 Upcoming |

---

## What This Project Builds

| Feature | Description |
|---------|-------------|
| 📄 **Resume Parsing** | Upload PDF/DOCX resumes; extract technical skills automatically |
| 🎯 **Job Matching** | Score your profile against thousands of IT job postings |
| 📉 **Skill Gap Analysis** | Identify missing skills ranked by market demand and salary impact |
| 🏆 **Role Recommendations** | Discover your best-fit job titles with match percentages |
| 📊 **Market Analytics** | Explore in-demand skills, salary trends, and location insights |
| 🗺️ **Learning Roadmap** | Get a personalized, prerequisite-ordered upskilling path |

---

## Technology Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Language | Python 3.13 |
| Web Framework | FastAPI 0.115 + Uvicorn |
| Configuration | Pydantic-Settings v2 |
| Data Analysis | Pandas, NumPy, Scikit-learn *(Day 6+)* |
| Database | SQLAlchemy + SQLite → PostgreSQL *(Day 3+)* |
| Resume Parsing | pdfminer.six *(Day 8+)* |
| Testing | Pytest + Starlette TestClient |

### Frontend *(Day 17+)*
| Layer | Technology |
|-------|-----------|
| Framework | React (Vite) |
| Charting | Recharts / Chart.js |
| Styling | CSS Modules |

---

## Project Structure

```
skill_gap_analyzer/
│
├── backend/                     # Python FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   └── health.py        # Health check endpoint
│   │   │       └── router.py            # v1 router aggregator
│   │   ├── core/
│   │   │   └── config.py               # Pydantic settings
│   │   ├── models/                      # ORM models (Day 3+)
│   │   └── main.py                      # FastAPI app factory
│   ├── tests/
│   │   ├── conftest.py                  # Shared pytest fixtures
│   │   ├── test_config.py               # Settings unit tests
│   │   ├── test_health.py               # Health endpoint tests
│   │   └── test_app_factory.py          # Application factory tests
│   ├── .env.example                     # Environment variable template
│   ├── pyproject.toml                   # Pytest configuration
│   ├── requirements.txt                 # Production dependencies
│   ├── requirements-dev.txt             # Development dependencies
│   └── main.py                          # Uvicorn entry point
│
├── docs/
│   ├── PROJECT_SPEC.md                  # Full functional requirements
│   ├── ROADMAP.md                       # 30-day development milestones
│   └── ARCHITECTURE.md                  # System design and ADRs
│
├── .gitignore
└── README.md
```

---

## Quick Start (Day 1 — Backend Only)

### Prerequisites
- Python 3.10+ (developed on 3.13)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/KrithikaPoojary/skill_gap_analyzer.git
cd skill_gap_analyzer
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env if needed — defaults work for local development
```

### 5. Start the development server

```bash
python main.py
# Or: uvicorn app.main:app --reload
```

Visit:
- API: `http://localhost:8000/api/v1/health`
- Swagger Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 6. Run the test suite

```bash
python -m pytest tests/ -v
```

Expected output: **27 tests passing** ✅

---

## API Endpoints (Day 1)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Application liveness check |
| `GET` | `/docs` | Interactive Swagger UI |
| `GET` | `/openapi.json` | OpenAPI 3.0 schema |

### Health Check Response Example

```json
{
  "status": "healthy",
  "app_name": "Job Market Intelligence & Skill Gap Analyzer",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-09-08T03:30:00.000000+00:00"
}
```

---

## Development Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_SPEC.md](docs/PROJECT_SPEC.md) | Full functional and non-functional requirements |
| [ROADMAP.md](docs/ROADMAP.md) | 30-day milestone tracker |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, ADRs, and layer responsibilities |

---

## Development Progress

This project is built incrementally over **30 development days** with exactly **10 meaningful Git commits per day**, simulating a realistic professional development history.

Each day's work is independently tested, documented, and committed before the next phase begins.

---

## Author

**Krithika Poojary**
- GitHub: [@KrithikaPoojary](https://github.com/KrithikaPoojary)

---

## License

MIT License — see [LICENSE](LICENSE) for details.
