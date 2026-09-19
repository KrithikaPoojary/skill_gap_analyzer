"""Integration tests for Resume Ingestion API endpoints (/api/v1/resume/*)."""

from __future__ import annotations

import io
import zipfile

import pytest
from starlette.testclient import TestClient

from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _txt_file(text: str = "Jane Doe\njane@example.com\nSkills\nPython, Docker") -> bytes:
    return text.encode("utf-8")


def _minimal_docx() -> bytes:
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
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body>"
            "<w:p><w:r><w:t>Alice Smith</w:t></w:r></w:p>"
            "<w:p><w:r><w:t>Skills</w:t></w:r></w:p>"
            "<w:p><w:r><w:t>Python, FastAPI, Docker</w:t></w:r></w:p>"
            "</w:body>"
            "</w:document>",
        )
        zf.writestr(
            "word/_rels/document.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            "</Relationships>",
        )
    return buf.getvalue()


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app=app, base_url="http://testserver") as c:
        yield c


# ---------------------------------------------------------------------------
# POST /api/v1/resume/parse
# ---------------------------------------------------------------------------


class TestParseEndpoint:
    def test_parse_txt_200(self, client):
        content = _txt_file("Jane Doe\njane@example.com\nSkills\nPython, Docker")
        resp = client.post(
            "/api/v1/resume/parse",
            files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 200

    def test_parse_response_schema(self, client):
        content = _txt_file()
        resp = client.post(
            "/api/v1/resume/parse",
            files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
        )
        body = resp.json()
        assert "filename" in body
        assert "char_count" in body
        assert "sections_found" in body
        assert "contact" in body
        assert "skills_raw" in body

    def test_parse_filename_in_response(self, client):
        content = _txt_file()
        resp = client.post(
            "/api/v1/resume/parse",
            files={"file": ("my_cv.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.json()["filename"] == "my_cv.txt"

    def test_parse_docx_200(self, client):
        content = _minimal_docx()
        resp = client.post(
            "/api/v1/resume/parse",
            files={"file": ("resume.docx", io.BytesIO(content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
        assert resp.status_code == 200

    def test_parse_unsupported_format_422(self, client):
        resp = client.post(
            "/api/v1/resume/parse",
            files={"file": ("resume.xlsx", io.BytesIO(b"data"), "application/vnd.ms-excel")},
        )
        assert resp.status_code == 422

    def test_parse_empty_file_400_or_422(self, client):
        resp = client.post(
            "/api/v1/resume/parse",
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )
        assert resp.status_code in (400, 422)

    def test_parse_contact_email_extracted(self, client):
        content = _txt_file("Jane Doe\njane@example.com\nSkills\nPython")
        resp = client.post(
            "/api/v1/resume/parse",
            files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.json()["contact"]["email"] == "jane@example.com"

    def test_parse_skills_list(self, client):
        content = _txt_file("Skills\nPython, Docker, FastAPI")
        resp = client.post(
            "/api/v1/resume/parse",
            files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
        )
        skills = resp.json()["skills_raw"]
        assert isinstance(skills, list)

    def test_parse_raw_text_preview_bounded(self, client):
        content = _txt_file("A" * 1000)
        resp = client.post(
            "/api/v1/resume/parse",
            files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
        )
        assert len(resp.json()["raw_text_preview"]) <= 500


# ---------------------------------------------------------------------------
# POST /api/v1/resume/ingest – happy-path smoke tests (no real DB needed
# because we mock the service layer)
# ---------------------------------------------------------------------------


class TestIngestEndpoint:
    def test_ingest_missing_user_id_422(self, client):
        """user_id is a required form field; omitting it yields 422."""
        content = _txt_file()
        resp = client.post(
            "/api/v1/resume/ingest",
            files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 422

    def test_ingest_unsupported_format_422(self, client):
        resp = client.post(
            "/api/v1/resume/ingest",
            data={"user_id": "1"},
            files={"file": ("resume.xlsx", io.BytesIO(b"data"), "application/octet-stream")},
        )
        assert resp.status_code == 422

    def test_ingest_invalid_user_id_type_422(self, client):
        content = _txt_file()
        resp = client.post(
            "/api/v1/resume/ingest",
            data={"user_id": "not-a-number"},
            files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 422

    def test_ingest_zero_user_id_422(self, client):
        content = _txt_file()
        resp = client.post(
            "/api/v1/resume/ingest",
            data={"user_id": "0"},
            files={"file": ("resume.txt", io.BytesIO(content), "text/plain")},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# OpenAPI registration check
# ---------------------------------------------------------------------------


def test_resume_routes_in_openapi(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/api/v1/resume/parse" in paths
    assert "/api/v1/resume/ingest" in paths
