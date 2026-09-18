"""Curated Learning Resource Catalog and Study Effort Estimator.

Maintains verified high-yield learning resources, documentation links,
practice project suggestions, difficulty tiers, and estimated study hours
for technical skills.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _norm(name: str) -> str:
    return " ".join(name.strip().lower().replace("-", " ").replace(".", "").split())


@dataclass(frozen=True)
class LearningResource:
    """A verified learning asset (tutorial, doc, course)."""

    title: str
    url: str
    resource_type: str = "official_docs"  # official_docs, course, interactive, book, video
    is_free: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "resource_type": self.resource_type,
            "is_free": self.is_free,
        }


@dataclass(frozen=True)
class SkillLearningMetadata:
    """Rich learning curriculum metadata for a specific skill."""

    skill_name: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    estimated_hours: int
    recommended_practice: str
    resources: list[LearningResource] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "category": self.category,
            "difficulty": self.difficulty,
            "estimated_hours": self.estimated_hours,
            "recommended_practice": self.recommended_practice,
            "resources": [r.to_dict() for r in self.resources],
        }


class LearningResourceCatalog:
    """Catalog of verified learning curricula and study effort expectations."""

    _CATALOG: dict[str, SkillLearningMetadata] = {
        "python": SkillLearningMetadata(
            skill_name="Python",
            category="language",
            difficulty="beginner",
            estimated_hours=30,
            recommended_practice="Implement CLI tools, parse JSON/CSV datasets, and write object-oriented modules.",
            resources=[
                LearningResource("Official Python Tutorial", "https://docs.python.org/3/tutorial/", "official_docs"),
                LearningResource("Python Morsels / Real Python", "https://realpython.com/", "interactive"),
            ],
        ),
        "fastapi": SkillLearningMetadata(
            skill_name="FastAPI",
            category="framework",
            difficulty="intermediate",
            estimated_hours=20,
            recommended_practice="Build an asynchronous CRUD REST API with Pydantic validation, dependency injection, and JWT auth.",
            resources=[
                LearningResource("FastAPI Official Documentation", "https://fastapi.tiangolo.com/", "official_docs"),
                LearningResource("Building High-Performance APIs with FastAPI", "https://realpython.com/fastapi-python-web-apis/", "course"),
            ],
        ),
        "docker": SkillLearningMetadata(
            skill_name="Docker",
            category="cloud_devops",
            difficulty="intermediate",
            estimated_hours=18,
            recommended_practice="Write multi-stage Dockerfiles for Python/Node apps and compose multi-container services with Docker Compose.",
            resources=[
                LearningResource("Docker Getting Started Guide", "https://docs.docker.com/get-started/", "official_docs"),
                LearningResource("Play with Docker Classroom", "https://labs.play-with-docker.com/", "interactive"),
            ],
        ),
        "kubernetes": SkillLearningMetadata(
            skill_name="Kubernetes",
            category="cloud_devops",
            difficulty="advanced",
            estimated_hours=35,
            recommended_practice="Deploy Pods, Deployments, Services, and Ingress on a local Minikube/Kind cluster with ConfigMaps and Secrets.",
            resources=[
                LearningResource("Kubernetes Documentation & Tutorials", "https://kubernetes.io/docs/tutorials/", "official_docs"),
                LearningResource("KubeAcademy", "https://kube.academy/", "course"),
            ],
        ),
        "postgresql": SkillLearningMetadata(
            skill_name="PostgreSQL",
            category="database",
            difficulty="intermediate",
            estimated_hours=22,
            recommended_practice="Design normalized relational schemas, write complex JOINs/window functions, and optimize query indexes with EXPLAIN ANALYZE.",
            resources=[
                LearningResource("PostgreSQL Official Documentation", "https://www.postgresql.org/docs/", "official_docs"),
                LearningResource("PostgreSQL Tutorial", "https://www.postgresqltutorial.com/", "interactive"),
            ],
        ),
        "sql": SkillLearningMetadata(
            skill_name="SQL",
            category="database",
            difficulty="beginner",
            estimated_hours=15,
            recommended_practice="Solve 50+ aggregate, join, subquery, and window function exercises on LeetCode or Mode Analytics.",
            resources=[
                LearningResource("Mode Analytics SQL Tutorial", "https://mode.com/sql-tutorial/", "interactive"),
                LearningResource("SQLZoo Interactive Lessons", "https://sqlzoo.net/", "interactive"),
            ],
        ),
        "react": SkillLearningMetadata(
            skill_name="React",
            category="framework",
            difficulty="intermediate",
            estimated_hours=25,
            recommended_practice="Construct a responsive single-page application leveraging hooks (useState, useEffect, useContext) and custom reusable components.",
            resources=[
                LearningResource("React.dev Official Docs & Interactive Sandbox", "https://react.dev/", "official_docs"),
                LearningResource("Fullstack Open (University of Helsinki)", "https://fullstackopen.com/en/", "course"),
            ],
        ),
        "typescript": SkillLearningMetadata(
            skill_name="TypeScript",
            category="language",
            difficulty="intermediate",
            estimated_hours=18,
            recommended_practice="Migrate a JavaScript project to TypeScript with strict compiler options, interfaces, and generics.",
            resources=[
                LearningResource("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/", "official_docs"),
                LearningResource("Total TypeScript Interactive Lessons", "https://www.totaltypescript.com/", "interactive"),
            ],
        ),
        "javascript": SkillLearningMetadata(
            skill_name="JavaScript",
            category="language",
            difficulty="beginner",
            estimated_hours=25,
            recommended_practice="Master ES6+ syntax, asynchronous programming (Promises, async/await), and DOM manipulation.",
            resources=[
                LearningResource("MDN Web Docs: JavaScript", "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "official_docs"),
                LearningResource("javascript.info", "https://javascript.info/", "interactive"),
            ],
        ),
        "pandas": SkillLearningMetadata(
            skill_name="Pandas",
            category="ai_ml",
            difficulty="intermediate",
            estimated_hours=18,
            recommended_practice="Load, clean, transform, and aggregate real-world tabular datasets using groupby, pivot tables, and time-series methods.",
            resources=[
                LearningResource("Pandas User Guide", "https://pandas.pydata.org/docs/user_guide/", "official_docs"),
                LearningResource("Kaggle Pandas Micro-Course", "https://www.kaggle.com/learn/pandas", "interactive"),
            ],
        ),
        "scikit learn": SkillLearningMetadata(
            skill_name="Scikit-learn",
            category="ai_ml",
            difficulty="intermediate",
            estimated_hours=24,
            recommended_practice="Implement end-to-end ML pipelines including feature scaling, cross-validation, hyperparameter grid search, and evaluation metrics.",
            resources=[
                LearningResource("Scikit-learn User Guide", "https://scikit-learn.org/stable/user_guide.html", "official_docs"),
                LearningResource("Kaggle Intro to Machine Learning", "https://www.kaggle.com/learn/intro-to-machine-learning", "interactive"),
            ],
        ),
        "pytorch": SkillLearningMetadata(
            skill_name="PyTorch",
            category="ai_ml",
            difficulty="advanced",
            estimated_hours=32,
            recommended_practice="Train custom neural networks using autograd, Dataset/DataLoader abstractions, and deploy with TorchScript.",
            resources=[
                LearningResource("PyTorch Official Tutorials", "https://pytorch.org/tutorials/", "official_docs"),
                LearningResource("Deep Learning with PyTorch (fast.ai)", "https://course.fast.ai/", "course"),
            ],
        ),
        "git": SkillLearningMetadata(
            skill_name="Git",
            category="cloud_devops",
            difficulty="beginner",
            estimated_hours=10,
            recommended_practice="Practice branching, merging, rebasing, resolving merge conflicts, and managing remote repositories.",
            resources=[
                LearningResource("Pro Git Book", "https://git-scm.com/book/en/v2", "book"),
                LearningResource("Learn Git Branching", "https://learngitbranching.js.org/", "interactive"),
            ],
        ),
        "linux": SkillLearningMetadata(
            skill_name="Linux",
            category="cloud_devops",
            difficulty="beginner",
            estimated_hours=15,
            recommended_practice="Navigate filesystem, manage permissions, write Bash scripts, and monitor system processes via terminal.",
            resources=[
                LearningResource("Linux Journey", "https://linuxjourney.com/", "interactive"),
                LearningResource("Bash Guide for Beginners", "https://tldp.org/LDP/Bash-Beginners-Guide/html/", "official_docs"),
            ],
        ),
        "aws": SkillLearningMetadata(
            skill_name="AWS",
            category="cloud_devops",
            difficulty="intermediate",
            estimated_hours=30,
            recommended_practice="Deploy architectures on EC2, S3, RDS, Lambda, and IAM using the AWS Free Tier and CloudFormation or Terraform.",
            resources=[
                LearningResource("AWS Skill Builder Free Tier", "https://explore.skillbuilder.aws/", "course"),
                LearningResource("AWS Architecture Center", "https://aws.amazon.com/architecture/", "official_docs"),
            ],
        ),
        "redis": SkillLearningMetadata(
            skill_name="Redis",
            category="database",
            difficulty="intermediate",
            estimated_hours=12,
            recommended_practice="Implement caching layers, session management, rate limiting, and Pub/Sub queues with Redis data structures.",
            resources=[
                LearningResource("Redis University", "https://university.redis.com/", "course"),
                LearningResource("Redis Documentation", "https://redis.io/docs/", "official_docs"),
            ],
        ),
    }

    def get_skill_metadata(self, skill_name: str) -> SkillLearningMetadata:
        """Fetch curated metadata for a skill, or generate sensible defaults."""
        key = _norm(skill_name)
        if key in self._CATALOG:
            return self._CATALOG[key]

        # Sensible dynamic fallback for uncataloged skills
        clean_title = skill_name.strip()
        encoded = clean_title.replace(" ", "+")
        return SkillLearningMetadata(
            skill_name=clean_title,
            category="other",
            difficulty="intermediate",
            estimated_hours=18,
            recommended_practice=f"Build a focused proof-of-concept application demonstrating core features of {clean_title}.",
            resources=[
                LearningResource(
                    title=f"{clean_title} Official Documentation",
                    url=f"https://www.google.com/search?q={encoded}+documentation",
                    resource_type="official_docs",
                ),
            ],
        )

    def get_total_estimated_hours(self, skills: list[str]) -> int:
        """Calculate total hours required to learn a set of skills."""
        return sum(self.get_skill_metadata(s).estimated_hours for s in skills)


learning_resource_catalog = LearningResourceCatalog()
