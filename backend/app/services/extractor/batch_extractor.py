"""Batch text and document skill extraction utility.

Processes batches of job postings or resumes, calculating aggregate extraction
frequency and performance metrics with per-document fault isolation.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
import time
from typing import Any

from app.services.skill_extractor import ExtractedSkill, skill_extractor


@dataclass(frozen=True)
class BatchDocumentResult:
    """Extraction output for an individual document in a batch."""

    doc_id: str
    total_skills: int
    skills: list[ExtractedSkill]

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "total_skills": self.total_skills,
            "skills": [s.to_dict() for s in self.skills],
        }


@dataclass(frozen=True)
class BatchSummaryReport:
    """Aggregate statistics across an entire extraction batch."""

    total_documents: int
    total_skills_extracted: int
    skill_frequency: dict[str, int]
    avg_skills_per_document: float
    total_duration_ms: float
    document_results: list[BatchDocumentResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_documents": self.total_documents,
            "total_skills_extracted": self.total_skills_extracted,
            "skill_frequency": self.skill_frequency,
            "avg_skills_per_document": self.avg_skills_per_document,
            "total_duration_ms": self.total_duration_ms,
            "document_results": [r.to_dict() for r in self.document_results],
        }


class BatchSkillExtractor:
    """Processes document batches for skill extraction with performance telemetry."""

    def extract_batch(
        self,
        documents: list[tuple[str, str]],  # (doc_id, text)
        *,
        min_confidence: float = 0.60,
    ) -> BatchSummaryReport:
        """Extract skills across a collection of documents."""
        start_time = time.perf_counter()
        doc_results: list[BatchDocumentResult] = []
        overall_counter: Counter[str] = Counter()

        for doc_id, text in documents:
            try:
                skills = skill_extractor.extract_skills(text, min_confidence=min_confidence)
            except Exception:
                skills = []

            for s in skills:
                overall_counter[s.name] += 1

            doc_results.append(
                BatchDocumentResult(
                    doc_id=doc_id,
                    total_skills=len(skills),
                    skills=skills,
                )
            )

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        total_docs = len(documents)
        total_skills = sum(r.total_skills for r in doc_results)
        avg_skills = round(total_skills / total_docs, 2) if total_docs > 0 else 0.0

        return BatchSummaryReport(
            total_documents=total_docs,
            total_skills_extracted=total_skills,
            skill_frequency=dict(overall_counter.most_common()),
            avg_skills_per_document=avg_skills,
            total_duration_ms=duration_ms,
            document_results=doc_results,
        )


batch_skill_extractor = BatchSkillExtractor()
