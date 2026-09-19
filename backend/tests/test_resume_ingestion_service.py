"""Unit tests for ResumeIngestionService (parse_only, no DB required)."""

from __future__ import annotations

import io
import zipfile

import pytest

from app.schemas.resume import ResumeParseResponse, ContactInfoSchema
from app.services.resume_ingestion_service import ResumeIngestionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _txt(text: str) -> bytes:
    return text.encode("utf-8")


def _minimal_docx(body_text: str = "Python Developer\nSkills: Python, FastAPI") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        lines = body_text.split("\n")
        paras = "".join(
            f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for line in lines
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body>{paras}</w:body>"
            "</w:document>",
        )
        zf.writestr(
            "word/_rels/document.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            "</Relationships>",
        )
    return buf.getvalue()


FULL_RESUME_TEXT = """Jane Doe
San Francisco, CA
jane@example.com
+1-800-555-9999
https://linkedin.com/in/janedoe
https://github.com/janedoe

Summary
Full-stack developer with 7 years of experience.

Skills
Python, React, PostgreSQL, Docker, AWS

Experience
Lead Developer - TechCorp (2019-Present)
Architected cloud-native applications.

Education
M.Sc. Software Engineering, Bay University, 2016
"""


# ---------------------------------------------------------------------------
# parse_only: TXT
# ---------------------------------------------------------------------------


class TestParseOnlyTxt:
    def setup_method(self):
        self.svc = ResumeIngestionService()

    def test_returns_parse_response(self):
        result = self.svc.parse_only(_txt(FULL_RESUME_TEXT), "resume.txt")
        assert isinstance(result, ResumeParseResponse)

    def test_filename_preserved(self):
        result = self.svc.parse_only(_txt(FULL_RESUME_TEXT), "resume.txt")
        assert result.filename == "resume.txt"

    def test_file_size(self):
        content = _txt(FULL_RESUME_TEXT)
        result = self.svc.parse_only(content, "resume.txt")
        assert result.file_size_bytes == len(content)

    def test_char_count_positive(self):
        result = self.svc.parse_only(_txt(FULL_RESUME_TEXT), "resume.txt")
        assert result.char_count > 0

    def test_sections_found(self):
        result = self.svc.parse_only(_txt(FULL_RESUME_TEXT), "resume.txt")
        assert "skills" in result.sections_found

    def test_contact_email(self):
        result = self.svc.parse_only(_txt(FULL_RESUME_TEXT), "resume.txt")
        assert result.contact.email == "jane@example.com"

    def test_skills_raw_populated(self):
        result = self.svc.parse_only(_txt(FULL_RESUME_TEXT), "resume.txt")
        assert "Python" in result.skills_raw

    def test_raw_text_preview_max_500(self):
        result = self.svc.parse_only(_txt(FULL_RESUME_TEXT), "resume.txt")
        assert len(result.raw_text_preview) <= 500

    def test_contact_is_schema(self):
        result = self.svc.parse_only(_txt(FULL_RESUME_TEXT), "resume.txt")
        assert isinstance(result.contact, ContactInfoSchema)


# ---------------------------------------------------------------------------
# parse_only: DOCX
# ---------------------------------------------------------------------------


class TestParseOnlyDocx:
    def setup_method(self):
        self.svc = ResumeIngestionService()

    def test_docx_parsed(self):
        content = _minimal_docx("Python Developer\nSkills\nPython, Docker")
        result = self.svc.parse_only(content, "resume.docx")
        assert result.char_count > 0

    def test_docx_skills_extracted(self):
        content = _minimal_docx("Alice Brown\nSkills\nPython, Docker, Kubernetes")
        result = self.svc.parse_only(content, "resume.docx")
        assert "Python" in result.skills_raw or len(result.skills_raw) > 0


# ---------------------------------------------------------------------------
# parse_only: error cases
# ---------------------------------------------------------------------------


class TestParseOnlyErrors:
    def setup_method(self):
        self.svc = ResumeIngestionService()

    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError):
            self.svc.parse_only(b"data", "resume.rtf")

    def test_empty_file_raises(self):
        with pytest.raises(ValueError):
            self.svc.parse_only(b"", "resume.txt")

    def test_oversized_file_raises(self):
        from app.services.document_parser import DocumentParser
        tiny_parser = DocumentParser(max_size_bytes=10)
        svc = ResumeIngestionService(parser=tiny_parser)
        with pytest.raises(ValueError, match="exceeds"):
            svc.parse_only(b"x" * 100, "resume.txt")


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


def test_singleton():
    from app.services.resume_ingestion_service import resume_ingestion_service
    assert resume_ingestion_service is not None
    assert isinstance(resume_ingestion_service, ResumeIngestionService)
