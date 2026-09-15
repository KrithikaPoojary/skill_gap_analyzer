"""Pydantic request and response validation schemas for skill extraction."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SkillExtractionItemSchema(BaseModel):
    """Schema representing an individual extracted skill."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Canonical name of the detected skill")
    category: str = Field(..., description="Taxonomy classification category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence score (0.0 to 1.0)")
    occurrences: int = Field(..., ge=1, description="Number of times skill or its aliases appeared")
    matched_variants: list[str] = Field(default_factory=list, description="Specific terms found in the text")
    context_snippets: list[str] = Field(
        default_factory=list,
        description="Short surrounding text excerpts where the skill was detected",
    )


class SkillExtractionRequest(BaseModel):
    """Request payload for extracting skills from a single text document."""

    text: str = Field(..., min_length=1, description="Raw job description or resume text")
    min_confidence: float = Field(
        0.60,
        ge=0.10,
        le=1.0,
        description="Minimum confidence score threshold",
    )


class SkillExtractionResponse(BaseModel):
    """Response payload returning detected skills from a single document."""

    total_extracted: int = Field(..., description="Count of distinct skills identified")
    skills: list[SkillExtractionItemSchema] = Field(..., description="Extracted skills list")
    processing_time_ms: float = Field(..., ge=0.0, description="Elapsed execution time in milliseconds")


class BatchExtractionDocument(BaseModel):
    """Single document entry within a batch extraction request."""

    id: str = Field(..., description="Unique client identifier for this document")
    text: str = Field(..., min_length=1, description="Document body text")


class BatchExtractionRequest(BaseModel):
    """Request payload for extracting skills from multiple documents simultaneously."""

    documents: list[BatchExtractionDocument] = Field(default_factory=list, max_length=100)
    min_confidence: float = Field(0.60, ge=0.10, le=1.0)


class BatchExtractionResultItem(BaseModel):
    """Extracted results corresponding to a single document in a batch."""

    id: str
    total_skills: int
    skills: list[SkillExtractionItemSchema]


class BatchExtractionResponse(BaseModel):
    """Response payload for multi-document batch skill extraction."""

    total_documents: int
    total_skills_found: int
    results: list[BatchExtractionResultItem]
    processing_time_ms: float
