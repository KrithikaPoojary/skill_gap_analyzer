"""Skill normalizer and taxonomy dictionary service.

Provides canonical normalization, alias mapping, and category classification
for technical and soft skills in the IT job market.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.models.skill import Skill, SkillCategory


class SkillDefinition(NamedTuple):
    """Canonical representation of a recognized technical skill."""

    canonical_name: str
    category: SkillCategory
    aliases: tuple[str, ...] = ()


# Comprehensive taxonomy of industry-standard tech skills
TAXONOMY_CATALOG: list[SkillDefinition] = [
    # Languages
    SkillDefinition("Python", SkillCategory.LANGUAGE, ("py", "python3", "python 3")),
    SkillDefinition("JavaScript", SkillCategory.LANGUAGE, ("js", "ecmascript", "es6", "es2015")),
    SkillDefinition("TypeScript", SkillCategory.LANGUAGE, ("ts", "typescript 4", "typescript 5")),
    SkillDefinition("Java", SkillCategory.LANGUAGE, ("java 11", "java 17", "java 21", "core java")),
    SkillDefinition("Go", SkillCategory.LANGUAGE, ("golang", "go-lang")),
    SkillDefinition("C++", SkillCategory.LANGUAGE, ("cpp", "c plus plus")),
    SkillDefinition("C#", SkillCategory.LANGUAGE, ("c-sharp", "csharp", "dotnet c#")),
    SkillDefinition("Rust", SkillCategory.LANGUAGE, ("rustlang",)),
    SkillDefinition("Ruby", SkillCategory.LANGUAGE, ("ruby on rails", "ruby-lang")),
    SkillDefinition("PHP", SkillCategory.LANGUAGE, ("php7", "php8")),
    SkillDefinition("Kotlin", SkillCategory.LANGUAGE, ("kotlin-lang",)),
    SkillDefinition("Swift", SkillCategory.LANGUAGE, ("swiftlang", "apple swift")),
    SkillDefinition("SQL", SkillCategory.LANGUAGE, ("structured query language", "ansi sql")),
    SkillDefinition("Bash", SkillCategory.LANGUAGE, ("shell", "sh", "zsh", "bash scripting")),

    # Frameworks & Libraries
    SkillDefinition("React", SkillCategory.FRAMEWORK, ("reactjs", "react.js", "react native")),
    SkillDefinition("FastAPI", SkillCategory.FRAMEWORK, ("fast-api", "fast api")),
    SkillDefinition("Django", SkillCategory.FRAMEWORK, ("django rest framework", "drf")),
    SkillDefinition("Flask", SkillCategory.FRAMEWORK, ()),
    SkillDefinition("Node.js", SkillCategory.FRAMEWORK, ("nodejs", "node", "node js")),
    SkillDefinition("Express.js", SkillCategory.FRAMEWORK, ("express", "expressjs")),
    SkillDefinition("Next.js", SkillCategory.FRAMEWORK, ("nextjs", "next")),
    SkillDefinition("Vue.js", SkillCategory.FRAMEWORK, ("vue", "vuejs", "vue 3")),
    SkillDefinition("Angular", SkillCategory.FRAMEWORK, ("angularjs", "angular 2+")),
    SkillDefinition("Spring Boot", SkillCategory.FRAMEWORK, ("springboot", "spring", "spring framework")),
    SkillDefinition(".NET", SkillCategory.FRAMEWORK, ("dotnet", ".net core", "asp.net", "asp.net core")),
    SkillDefinition("NestJS", SkillCategory.FRAMEWORK, ("nest.js", "nest")),
    SkillDefinition("Tailwind CSS", SkillCategory.FRAMEWORK, ("tailwind", "tailwindcss")),
    SkillDefinition("GraphQL", SkillCategory.FRAMEWORK, ("graphql api", "apollo")),

    # Databases
    SkillDefinition("PostgreSQL", SkillCategory.DATABASE, ("postgres", "postgresql db", "psql")),
    SkillDefinition("MySQL", SkillCategory.DATABASE, ("mysql db", "mariadb")),
    SkillDefinition("MongoDB", SkillCategory.DATABASE, ("mongo", "mongodb atlas")),
    SkillDefinition("Redis", SkillCategory.DATABASE, ("redis cache",)),
    SkillDefinition("Elasticsearch", SkillCategory.DATABASE, ("elastic search", "opensearch")),
    SkillDefinition("DynamoDB", SkillCategory.DATABASE, ("aws dynamodb",)),
    SkillDefinition("SQLite", SkillCategory.DATABASE, ("sqlite3",)),
    SkillDefinition("Cassandra", SkillCategory.DATABASE, ("apache cassandra",)),
    SkillDefinition("Snowflake", SkillCategory.DATABASE, ("snowflake db",)),

    # Cloud & DevOps
    SkillDefinition("AWS", SkillCategory.CLOUD_DEVOPS, ("amazon web services", "amazon aws")),
    SkillDefinition("Azure", SkillCategory.CLOUD_DEVOPS, ("microsoft azure", "azure cloud")),
    SkillDefinition("GCP", SkillCategory.CLOUD_DEVOPS, ("google cloud", "google cloud platform")),
    SkillDefinition("Docker", SkillCategory.CLOUD_DEVOPS, ("docker containers", "dockerfile")),
    SkillDefinition("Kubernetes", SkillCategory.CLOUD_DEVOPS, ("k8s", "kube")),
    SkillDefinition("Terraform", SkillCategory.CLOUD_DEVOPS, ("hashicorp terraform", "tf")),
    SkillDefinition("Ansible", SkillCategory.CLOUD_DEVOPS, ()),
    SkillDefinition("CI/CD", SkillCategory.CLOUD_DEVOPS, ("cicd", "continuous integration", "github actions", "gitlab ci", "jenkins")),
    SkillDefinition("Linux", SkillCategory.CLOUD_DEVOPS, ("ubuntu", "debian", "redhat", "centos")),
    SkillDefinition("Git", SkillCategory.CLOUD_DEVOPS, ("github", "gitlab", "version control")),
    SkillDefinition("Kafka", SkillCategory.CLOUD_DEVOPS, ("apache kafka", "kafka streaming")),
    SkillDefinition("Prometheus", SkillCategory.CLOUD_DEVOPS, ("grafana", "monitoring")),

    # AI & Machine Learning
    SkillDefinition("Machine Learning", SkillCategory.AI_ML, ("ml", "applied ml")),
    SkillDefinition("Deep Learning", SkillCategory.AI_ML, ("neural networks",)),
    SkillDefinition("PyTorch", SkillCategory.AI_ML, ("torch",)),
    SkillDefinition("TensorFlow", SkillCategory.AI_ML, ("tf", "keras")),
    SkillDefinition("Scikit-Learn", SkillCategory.AI_ML, ("sklearn", "scikit learn")),
    SkillDefinition("Pandas", SkillCategory.AI_ML, ()),
    SkillDefinition("NumPy", SkillCategory.AI_ML, ()),
    SkillDefinition("NLP", SkillCategory.AI_ML, ("natural language processing", "llm", "transformers", "huggingface")),
    SkillDefinition("Computer Vision", SkillCategory.AI_ML, ("cv", "opencv")),
    SkillDefinition("LangChain", SkillCategory.AI_ML, ("langchain ai", "rag")),

    # Testing & QA
    SkillDefinition("Pytest", SkillCategory.TESTING, ("pytest runner",)),
    SkillDefinition("Jest", SkillCategory.TESTING, ()),
    SkillDefinition("Cypress", SkillCategory.TESTING, ()),
    SkillDefinition("Selenium", SkillCategory.TESTING, ()),
    SkillDefinition("Unit Testing", SkillCategory.TESTING, ("tdd", "unit tests", "automated testing")),

    # Methodologies & Soft Skills
    SkillDefinition("Agile", SkillCategory.METHODOLOGY, ("scrum", "kanban", "sprints")),
    SkillDefinition("REST API", SkillCategory.METHODOLOGY, ("restful", "restful api", "api design")),
    SkillDefinition("Microservices", SkillCategory.METHODOLOGY, ("microservice architecture", "distributed systems")),
    SkillDefinition("Problem Solving", SkillCategory.SOFT_SKILL, ("analytical skills", "critical thinking")),
    SkillDefinition("Communication", SkillCategory.SOFT_SKILL, ("written communication", "verbal communication")),
    SkillDefinition("Team Leadership", SkillCategory.SOFT_SKILL, ("mentorship", "tech lead", "leadership")),
]


def _build_alias_map() -> tuple[dict[str, SkillDefinition], dict[str, SkillDefinition]]:
    """Build fast lookup dictionaries for canonical names and aliases."""
    canon_map: dict[str, SkillDefinition] = {}
    alias_map: dict[str, SkillDefinition] = {}

    for item in TAXONOMY_CATALOG:
        canon_slug = normalize_text(item.canonical_name)
        canon_map[canon_slug] = item
        alias_map[canon_slug] = item
        for alias in item.aliases:
            alias_slug = normalize_text(alias)
            alias_map[alias_slug] = item

    return canon_map, alias_map


def normalize_text(text: str) -> str:
    """Normalize skill name into a clean, searchable slug.

    Trims whitespace, replaces punctuation with single spaces or drops them,
    collapses multiple spaces, and converts to lowercase.
    """
    if not text:
        return ""
    # Preserve key chars like +, #, ., /
    cleaned = text.strip().lower()
    # Replace separators like _ or - with space
    cleaned = re.sub(r"[\-_]+", " ", cleaned)
    # Remove unwanted punctuation, keeping characters like +, #, .
    cleaned = re.sub(r"[^\w\s\+\#\.]", "", cleaned)
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class SkillNormalizer:
    """Service to normalize, classify, and persist skills according to the taxonomy."""

    def __init__(self) -> None:
        self._canon_map, self._alias_map = _build_alias_map()

    def normalize(self, raw_name: str) -> tuple[str, str, SkillCategory]:
        """Resolve a raw skill string to canonical name, normalized slug, and category.

        Returns:
            Tuple of (canonical_name, normalized_name, category)
        """
        raw_clean = raw_name.strip()
        slug = normalize_text(raw_clean)

        if slug in self._alias_map:
            defn = self._alias_map[slug]
            return defn.canonical_name, normalize_text(defn.canonical_name), defn.category

        # If unknown, infer title-cased canonical name and fallback category
        inferred_name = " ".join(word.capitalize() for word in raw_clean.split())
        return inferred_name, slug if slug else normalize_text(inferred_name), SkillCategory.OTHER

    def resolve_or_create(self, db: Session, raw_name: str) -> Skill:
        """Find an existing skill by normalized name or create a new taxonomy entry."""
        canonical_name, slug, category = self.normalize(raw_name)

        # Check existing by normalized name or name
        skill = (
            db.query(Skill)
            .filter((Skill.normalized_name == slug) | (Skill.name == canonical_name))
            .first()
        )
        if skill:
            return skill

        # Lookup aliases from taxonomy if present
        aliases_str = None
        if slug in self._alias_map:
            aliases_str = ",".join(self._alias_map[slug].aliases)

        skill = Skill(
            name=canonical_name,
            normalized_name=slug,
            category=category.value,
            aliases=aliases_str,
            is_verified=category != SkillCategory.OTHER,
        )
        db.add(skill)
        db.flush()
        return skill


skill_normalizer = SkillNormalizer()
