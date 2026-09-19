"""Pydantic schemas for the Resume Ingestion Pipeline.

Defines request/response models for document upload, section parsing,
and the full resume ingestion workflow.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ResumeIngestRequest(BaseModel):
    """Optional metadata that can accompany a resume upload."""

    user_id: int = Field(..., ge=1, description="User to associate the resume with.")
    filename: str = Field(..., min_length=1, description="Original file name (e.g. resume.pdf).")
    content_type: Optional[str] = Field(None, description="MIME type of the uploaded file.")


# ---------------------------------------------------------------------------
# Contact info DTO
# ---------------------------------------------------------------------------


class ContactInfoSchema(BaseModel):
    """Extracted contact fields from the resume document."""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ResumeParseResponse(BaseModel):
    """Result of parsing and segmenting a single uploaded resume."""

    filename: str
    file_size_bytes: int
    char_count: int
    sections_found: list[str] = Field(
        default_factory=list,
        description="Section labels detected in the document.",
    )
    contact: ContactInfoSchema
    skills_raw: list[str] = Field(
        default_factory=list,
        description="Skill tokens extracted from the Skills section.",
    )
    raw_text_preview: str = Field(
        default="",
        description="First 500 characters of extracted text (for debugging).",
    )


class ResumeIngestResponse(BaseModel):
    """Full pipeline result after ingesting a resume for a user."""

    user_id: int
    filename: str
    file_size_bytes: int
    char_count: int
    sections_found: list[str]
    contact: ContactInfoSchema
    skills_raw: list[str]
    skills_matched: int = Field(
        0,
        description="Number of raw skill tokens successfully matched to taxonomy.",
    )
    skills_added: int = Field(
        0,
        description="Number of new user-skill associations created.",
    )
    profile_updated: bool = Field(
        False,
        description="True if the user profile was updated with contact info.",
    )
    message: str = ""
