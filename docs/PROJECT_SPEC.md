# Job Market Intelligence & Skill Gap Analyzer
## Comprehensive Project Specification & System Requirements

### 1. Executive Summary
The **Job Market Intelligence & Skill Gap Analyzer** is an end-to-end analytical platform and decision-support system designed to empower IT professionals, career transitioners, and students. By synthesizing unstructured and semi-structured job postings from dynamic tech ecosystems, the system extracts critical skill requirements, evaluates an individual candidate's resume or skill profile, calculates quantitative match metrics, and produces an actionable, prioritized learning roadmap to bridge identified competency deficits.

---

### 2. User Personas & Problem Statements
| Persona | Background | Pain Point | System Value Proposition |
| :--- | :--- | :--- | :--- |
| **Aspiring Data Analyst / Developer** | Fresh graduate / self-taught learner | Unsure which tools/frameworks are actively valued vs. legacy technologies | Clear market-driven skill frequency rankings and role alignment scores |
| **Mid-Career Transitioner** | Experience in adjacent technical/analytical domain | Needs targeted upskilling path without wasting months on irrelevant certifications | Automated resume gap analysis highlighting high-ROI missing competencies |
| **Tech Professional (Upskilling)** | Employed engineer targeting senior or lead roles | Needs to know salary correlations and emerging tech stack requirements | Real-time salary-skill associations and strategic roadmap suggestions |

---

### 3. Functional Requirements

#### Module 1: Resume & Skill Profile Ingestion
- **1.1 Multi-format Parsing:** Support extraction of raw text from PDF and DOCX documents with robust handling of single/multi-column layouts.
- **1.2 Skill Entity Extraction:** Utilize pattern recognition and NLP dictionary-based matching to identify technical tools, languages, frameworks, databases, and methodologies.
- **1.3 Manual Override & Profile Management:** Allow users to curate extracted skills, add unlisted skills, indicate proficiency levels (Beginner, Intermediate, Advanced), and specify years of experience.

#### Module 2: IT Job Postings Data Pipeline
- **2.1 Standardized Schema:** Model job postings with attributes: `id`, `title`, `company`, `location`, `experience_level`, `min_salary`, `max_salary`, `currency`, `employment_type`, `required_skills`, `description`, and `posted_date`.
- **2.2 Data Cleaning & Normalization:** Standardize aliases (e.g., "JS" -> "JavaScript", "Postgres" -> "PostgreSQL", "React.js" -> "React").
- **2.3 Batch & Incremental Loading:** Enable continuous dataset ingestion from structured CSV/JSON archives.

#### Module 3: Quantitative Job Matching Engine
- **3.1 Base Skill Overlap Calculation:**
  $$\text{Match Score} = \left(\frac{|\text{User Skills} \cap \text{Required Skills}|}{|\text{Required Skills}|}\right) \times 100$$
- **3.2 Weighted Matching:** Distinguish core mandatory prerequisites from preferred qualifications.
- **3.3 Multi-factor Scoring:** Incorporate role seniority, years of experience, and geographic alignment into weighted score composite.

#### Module 4: Skill Gap & Priority Engine
- **4.1 Competency Segmentation:** Segment candidate skills into *Strong Matches*, *Partial/Adjacent Matches*, and *Deficits (Missing Skills)*.
- **4.2 Gap Prioritization Matrix:** Rank missing skills based on:
  - Market Demand Frequency (how often requested across postings)
  - Salary Impact (statistical coefficient in market postings)
  - Role Criticality (core vs. nice-to-have)
- **4.3 Priority Tiers:** High Priority (Immediate blocker), Medium Priority (Competitive advantage), Low Priority (Supplementary).

#### Module 5: Role Recommendation Engine
- **5.1 Target Role Mapping:** Evaluate candidate profile against target archetypes:
  - Data Analyst
  - Business Intelligence (BI) Analyst
  - Data Engineer
  - Python Backend Developer
  - Junior Full-Stack Software Engineer
- **5.2 Role Affinity Index:** Rank suitable roles by compatibility and upskilling feasibility.

#### Module 6: Market Intelligence & Analytics
- **6.1 Skill Frequency Distributions:** Aggregate top 20 skills overall and segmented by role.
- **6.2 Compensation Insights:** Correlate skill combinations with average, median, and 90th percentile salary benchmarks.
- **6.3 Geographic & Remote Trends:** Analyze distributed tech hubs vs. on-site concentration.

#### Module 7: Interactive Dashboard & Visualization
- **7.1 KPI Summary Bar:** Total analyzed jobs, average market salary, top trending skill, candidate match score.
- **7.2 Visual Charts:** Interactive distribution charts (bar charts, radar charts for skill gaps, heatmaps for salary distribution).
- **7.3 Responsive User Interface:** Modern, clean, accessible UI built for desktop and tablet viewports.

#### Module 8: Personalized Learning Roadmap Generator
- **8.1 Directed Dependency Graph:** Sequence missing competencies respecting technical prerequisites (e.g., Python Basics -> Pandas -> Machine Learning).
- **8.2 Milestone-Based Stages:** Provide progressive phases with recommended project concepts to prove mastery.

---

### 4. Non-Functional Requirements (NFR)
- **Performance:** Resume parsing within < 2 seconds; API response times for gap analysis < 250ms for 10,000 dataset records.
- **Security:** Strict file upload validation (MIME-type verification, maximum 5MB size limit); zero persistent storage of sensitive PII without user consent; sanitization of all inputs against XSS and injection.
- **Reliability:** Comprehensive automated test coverage (>80% target for business logic and scoring algorithms); graceful fallback when external services are unreachable.
- **Modularity:** Separation of concerns following domain-driven principles (API routes, services, data models, schemas, and analytics pipelines).
- **Maintainability:** Full PEP 8 compliance, type annotations (`typing`), docstrings on all public functions, and consistent semantic versioning.

---

### 5. Technical Constraints & Baseline Stack
- **Backend Language:** Python 3.10+ (tested on Python 3.13)
- **Web Framework:** FastAPI (Asynchronous ASGI framework)
- **Data Computation:** Pandas, NumPy, Scikit-learn
- **Testing:** Pytest, pytest-asyncio, HTTPX
- **Version Control:** Git, structured 30-day sequential evolution
