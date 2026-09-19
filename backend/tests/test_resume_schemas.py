"""Unit tests for Resume Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.resume import (
    ContactInfoSchema,
    ResumeIngestRequest,
    ResumeIngestResponse,
    ResumeParseResponse,
)


# ---------------------------------------------------------------------------
# ResumeIngestRequest
# ---------------------------------------------------------------------------


class TestResumeIngestRequest:
    def test_valid_minimal(self):
        req = ResumeIngestRequest(user_id=1, filename="resume.pdf")
        assert req.user_id == 1
        assert req.filename == "resume.pdf"
        assert req.content_type is None

    def test_with_content_type(self):
        req = ResumeIngestRequest(user_id=5, filename="cv.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert req.content_type is not None

    def test_user_id_must_be_positive(self):
        with pytest.raises(ValidationError):
            ResumeIngestRequest(user_id=0, filename="resume.pdf")

    def test_user_id_negative_rejected(self):
        with pytest.raises(ValidationError):
            ResumeIngestRequest(user_id=-1, filename="resume.pdf")

    def test_filename_cannot_be_empty(self):
        with pytest.raises(ValidationError):
            ResumeIngestRequest(user_id=1, filename="")

    def test_missing_user_id_rejected(self):
        with pytest.raises(ValidationError):
            ResumeIngestRequest(filename="resume.pdf")  # type: ignore[call-arg]

    def test_missing_filename_rejected(self):
        with pytest.raises(ValidationError):
            ResumeIngestRequest(user_id=1)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ContactInfoSchema
# ---------------------------------------------------------------------------


class TestContactInfoSchema:
    def test_all_none_defaults(self):
        c = ContactInfoSchema()
        assert c.name is None
        assert c.email is None
        assert c.phone is None
        assert c.linkedin_url is None
        assert c.github_url is None
        assert c.website_url is None
        assert c.location is None

    def test_full_contact(self):
        c = ContactInfoSchema(
            name="Jane Doe",
            email="jane@example.com",
            phone="+1-555-0001",
            linkedin_url="https://linkedin.com/in/janedoe",
            github_url="https://github.com/janedoe",
            website_url="https://janedoe.dev",
            location="New York, NY",
        )
        assert c.name == "Jane Doe"
        assert c.email == "jane@example.com"

    def test_partial_contact(self):
        c = ContactInfoSchema(email="only@email.com")
        assert c.email == "only@email.com"
        assert c.name is None


# ---------------------------------------------------------------------------
# ResumeParseResponse
# ---------------------------------------------------------------------------


class TestResumeParseResponse:
    def _make(self, **kwargs) -> ResumeParseResponse:
        defaults = {
            "filename": "resume.txt",
            "file_size_bytes": 1024,
            "char_count": 800,
            "sections_found": ["header", "skills", "experience"],
            "contact": ContactInfoSchema(email="j@example.com"),
            "skills_raw": ["Python", "Docker"],
        }
        defaults.update(kwargs)
        return ResumeParseResponse(**defaults)

    def test_valid_creation(self):
        r = self._make()
        assert r.filename == "resume.txt"

    def test_sections_is_list(self):
        r = self._make()
        assert isinstance(r.sections_found, list)

    def test_skills_raw_list(self):
        r = self._make()
        assert "Python" in r.skills_raw

    def test_default_preview_empty(self):
        r = self._make()
        assert r.raw_text_preview == ""

    def test_preview_populated(self):
        r = self._make(raw_text_preview="Hello World")
        assert r.raw_text_preview == "Hello World"

    def test_contact_embedded(self):
        r = self._make()
        assert r.contact.email == "j@example.com"


# ---------------------------------------------------------------------------
# ResumeIngestResponse
# ---------------------------------------------------------------------------


class TestResumeIngestResponse:
    def _make(self, **kwargs) -> ResumeIngestResponse:
        defaults = {
            "user_id": 1,
            "filename": "resume.txt",
            "file_size_bytes": 1024,
            "char_count": 800,
            "sections_found": ["header", "skills"],
            "contact": ContactInfoSchema(email="j@example.com"),
            "skills_raw": ["Python"],
            "skills_matched": 1,
            "skills_added": 1,
            "profile_updated": True,
            "message": "Done",
        }
        defaults.update(kwargs)
        return ResumeIngestResponse(**defaults)

    def test_valid_creation(self):
        r = self._make()
        assert r.user_id == 1
        assert r.skills_matched == 1
        assert r.skills_added == 1
        assert r.profile_updated is True

    def test_default_counts_zero(self):
        r = ResumeIngestResponse(
            user_id=2,
            filename="cv.pdf",
            file_size_bytes=500,
            char_count=300,
            sections_found=[],
            contact=ContactInfoSchema(),
            skills_raw=[],
        )
        assert r.skills_matched == 0
        assert r.skills_added == 0
        assert r.profile_updated is False
        assert r.message == ""

    def test_message_field(self):
        r = self._make(message="Parsed OK")
        assert r.message == "Parsed OK"
