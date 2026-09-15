"""Unit tests for skill extraction Pydantic schemas."""

import pytest

from app.schemas.extraction import (
    BatchExtractionDocument,
    BatchExtractionRequest,
    BatchExtractionResponse,
    BatchExtractionResultItem,
    SkillExtractionItemSchema,
    SkillExtractionRequest,
    SkillExtractionResponse,
)


class TestExtractionSchemas:
    """Test suite for extraction request and response schema validations."""

    def test_single_extraction_request_and_response(self) -> None:
        req = SkillExtractionRequest(text="Expert in Python and AWS.", min_confidence=0.7)
        assert req.min_confidence == 0.7

        item = SkillExtractionItemSchema(
            name="Python",
            category="language",
            confidence=0.95,
            occurrences=2,
            matched_variants=["Python", "py"],
        )
        resp = SkillExtractionResponse(
            total_extracted=1,
            skills=[item],
            processing_time_ms=12.4,
        )
        assert resp.total_extracted == 1
        assert resp.skills[0].name == "Python"
        assert resp.processing_time_ms == 12.4

    def test_batch_extraction_request_and_response(self) -> None:
        batch_req = BatchExtractionRequest(
            documents=[
                BatchExtractionDocument(id="doc-1", text="Python engineer"),
                BatchExtractionDocument(id="doc-2", text="React frontend developer"),
            ],
            min_confidence=0.6,
        )
        assert len(batch_req.documents) == 2

        batch_resp = BatchExtractionResponse(
            total_documents=2,
            total_skills_found=2,
            results=[
                BatchExtractionResultItem(
                    id="doc-1",
                    total_skills=1,
                    skills=[
                        SkillExtractionItemSchema(
                            name="Python",
                            category="language",
                            confidence=0.9,
                            occurrences=1,
                            matched_variants=["Python"],
                        )
                    ],
                )
            ],
            processing_time_ms=25.0,
        )
        assert batch_resp.total_documents == 2
        assert batch_resp.results[0].id == "doc-1"
