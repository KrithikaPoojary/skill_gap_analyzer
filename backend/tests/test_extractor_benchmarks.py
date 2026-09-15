"""Accuracy benchmarks for the SkillExtractor NLP pipeline.

Measures precision, recall, and F1 across a curated set of annotated
job-description fixtures.  These tests serve as a regression guard — any
future change to the pattern taxonomy or confidence scorer that drops F1
below the defined threshold will break the build.

Benchmark methodology:
  - "ground truth" is a hand-labelled set of canonical skill names that
    must appear in extraction results for each fixture text.
  - Precision   = |extracted ∩ expected| / |extracted|
  - Recall      = |extracted ∩ expected| / |expected|
  - F1          = 2 * precision * recall / (precision + recall)

Thresholds (conservative; tuned for the current in-memory taxonomy):
  - Minimum per-fixture recall : 0.75
  - Minimum overall F1         : 0.70
"""

from __future__ import annotations

import pytest

from app.services.skill_extractor import skill_extractor


# ---------------------------------------------------------------------------
# Annotated fixtures
# Each tuple: (fixture_id, text, {expected_canonical_skill_names})
# ---------------------------------------------------------------------------
BENCHMARK_FIXTURES: list[tuple[str, str, set[str]]] = [
    (
        "backend-python",
        """
        We are hiring a Senior Backend Engineer.
        Required: 5+ years Python, FastAPI or Django, PostgreSQL, Redis.
        Nice to have: Docker, Kubernetes, AWS or GCP experience.
        """,
        {"Python", "FastAPI", "Django", "PostgreSQL", "Redis", "Docker", "Kubernetes"},
    ),
    (
        "frontend-react",
        """
        Frontend Developer role open.
        Must know: React, TypeScript, HTML, CSS, and REST APIs.
        Bonus: GraphQL, Next.js, and Jest testing experience.
        """,
        {"React", "TypeScript", "HTML", "CSS", "GraphQL", "Next.js"},
    ),
    (
        "devops-cloud",
        """
        DevOps Engineer needed to manage our CI/CD pipelines.
        Expertise in Docker, Kubernetes, Terraform, Ansible, Jenkins required.
        Cloud: AWS or Azure preferred. Scripting in Python or Bash.
        """,
        {"Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "AWS", "Python", "Bash"},
    ),
    (
        "data-science",
        """
        Data Scientist position.
        Experience with Python, Pandas, NumPy, Scikit-learn, TensorFlow or PyTorch.
        SQL knowledge (PostgreSQL / MySQL) essential. Tableau a plus.
        """,
        {"Python", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "PostgreSQL", "MySQL"},
    ),
    (
        "fullstack-java",
        """
        Full-stack engineer with Java Spring Boot, React, and PostgreSQL.
        CI/CD with Jenkins and GitHub Actions.  Containerised with Docker.
        """,
        {"Java", "Spring Boot", "React", "PostgreSQL", "Jenkins", "Docker"},
    ),
    (
        "ml-nlp",
        """
        Machine Learning Engineer – NLP focus.
        Must have: Python, PyTorch, Hugging Face Transformers, BERT.
        Experience with vector databases (Pinecone, Weaviate) is a strong plus.
        """,
        {"Python", "PyTorch", "BERT"},
    ),
    (
        "mobile-ios",
        """
        iOS Developer.  Swift and Objective-C required.
        Familiarity with Xcode, Core Data, and REST APIs.
        Firebase or AWS Amplify for backend integration.
        """,
        {"Swift", "Objective-C", "Xcode", "Firebase", "AWS"},
    ),
    (
        "security-engineer",
        """
        Security Engineer with expertise in penetration testing,
        vulnerability assessment, Python scripting, and knowledge of OWASP Top 10.
        Familiarity with Kubernetes RBAC and AWS IAM policies.
        """,
        {"Python", "Kubernetes", "AWS"},
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_metrics(
    extracted_names: set[str], expected_names: set[str]
) -> dict[str, float]:
    tp = len(extracted_names & expected_names)
    precision = tp / len(extracted_names) if extracted_names else 0.0
    recall = tp / len(expected_names) if expected_names else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {"precision": precision, "recall": recall, "f1": f1}


# ---------------------------------------------------------------------------
# Per-fixture recall tests
# ---------------------------------------------------------------------------

class TestExtractionRecallPerFixture:
    """Each annotated fixture must achieve >= 75 % recall."""

    RECALL_THRESHOLD = 0.75

    @pytest.mark.parametrize(
        "fixture_id,text,expected",
        [(fid, txt, exp) for fid, txt, exp in BENCHMARK_FIXTURES],
        ids=[fid for fid, *_ in BENCHMARK_FIXTURES],
    )
    def test_recall_meets_threshold(
        self, fixture_id: str, text: str, expected: set[str]
    ) -> None:
        results = skill_extractor.extract_skills(text)
        extracted_names = {r.name for r in results}
        metrics = _compute_metrics(extracted_names, expected)

        assert metrics["recall"] >= self.RECALL_THRESHOLD, (
            f"[{fixture_id}] Recall {metrics['recall']:.2%} < {self.RECALL_THRESHOLD:.0%}\n"
            f"  Expected : {sorted(expected)}\n"
            f"  Extracted: {sorted(extracted_names)}\n"
            f"  Missed   : {sorted(expected - extracted_names)}"
        )


# ---------------------------------------------------------------------------
# Aggregate F1 across all fixtures
# ---------------------------------------------------------------------------

class TestOverallAggregateF1:
    """Macro-averaged F1 across all benchmark fixtures must be >= 0.70."""

    F1_THRESHOLD = 0.70

    def test_macro_f1_threshold(self) -> None:
        f1_scores: list[float] = []

        for fixture_id, text, expected in BENCHMARK_FIXTURES:
            results = skill_extractor.extract_skills(text)
            extracted_names = {r.name for r in results}
            metrics = _compute_metrics(extracted_names, expected)
            f1_scores.append(metrics["f1"])

        macro_f1 = sum(f1_scores) / len(f1_scores)
        assert macro_f1 >= self.F1_THRESHOLD, (
            f"Macro-averaged F1 {macro_f1:.2%} is below threshold {self.F1_THRESHOLD:.0%}.\n"
            f"Per-fixture F1 scores: { {fid: round(f1, 3) for (fid, *_), f1 in zip(BENCHMARK_FIXTURES, f1_scores)} }"
        )


# ---------------------------------------------------------------------------
# Confidence score sanity
# ---------------------------------------------------------------------------

class TestConfidenceScoreSanity:
    """All extracted skills must have valid confidence scores in [0, 1]."""

    def test_all_confidence_scores_in_range(self) -> None:
        text = (
            "Seeking a full-stack developer proficient in Python, React, "
            "Node.js, PostgreSQL, Docker, and AWS."
        )
        results = skill_extractor.extract_skills(text)
        assert len(results) > 0, "Expected at least one extracted skill"
        for skill in results:
            assert 0.0 <= skill.confidence <= 1.0, (
                f"Skill '{skill.name}' has invalid confidence {skill.confidence}"
            )

    def test_high_frequency_skills_have_higher_confidence(self) -> None:
        # Python mentioned 3× vs Haskell mentioned 1× — Python should score higher
        text = (
            "We use Python extensively. Python is central to our stack. "
            "Our ML pipelines are also written in Python. Haskell is rarely used."
        )
        results = skill_extractor.extract_skills(text)
        names = {r.name for r in results}
        if "Python" in names and "Haskell" in names:
            python_conf = next(r.confidence for r in results if r.name == "Python")
            haskell_conf = next(r.confidence for r in results if r.name == "Haskell")
            assert python_conf >= haskell_conf, (
                f"Expected Python ({python_conf}) to score >= Haskell ({haskell_conf})"
            )
