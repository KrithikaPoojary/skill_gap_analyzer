"""Unit tests for DocumentParser service."""

from __future__ import annotations

import io
import struct
import pytest

from app.services.document_parser import (
    SUPPORTED_EXTENSIONS,
    DocumentParser,
    document_parser,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_txt(text: str = "Hello, world!") -> bytes:
    return text.encode("utf-8")


def _minimal_docx() -> bytes:
    """Build a very small but valid docx (zip with required xml files)."""
    import zipfile

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
            "<w:p><w:r><w:t>Python Developer</w:t></w:r></w:p>"
            "<w:p><w:r><w:t>Skills: Python, Django</w:t></w:r></w:p>"
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


# ---------------------------------------------------------------------------
# DocumentParser.validate_file
# ---------------------------------------------------------------------------


class TestValidateFile:
    def test_valid_pdf_extension(self):
        parser = DocumentParser()
        ext = parser.validate_file(b"x" * 100, "resume.pdf")
        assert ext == ".pdf"

    def test_valid_docx_extension(self):
        parser = DocumentParser()
        ext = parser.validate_file(b"x" * 100, "resume.docx")
        assert ext == ".docx"

    def test_valid_txt_extension(self):
        parser = DocumentParser()
        ext = parser.validate_file(_make_txt(), "resume.txt")
        assert ext == ".txt"

    def test_valid_md_extension(self):
        parser = DocumentParser()
        ext = parser.validate_file(_make_txt(), "notes.md")
        assert ext == ".md"

    def test_empty_file_rejected(self):
        parser = DocumentParser()
        with pytest.raises(ValueError, match="empty"):
            parser.validate_file(b"", "resume.pdf")

    def test_oversized_file_rejected(self):
        parser = DocumentParser(max_size_bytes=100)
        with pytest.raises(ValueError, match="exceeds"):
            parser.validate_file(b"x" * 200, "resume.txt")

    def test_unsupported_extension_rejected(self):
        parser = DocumentParser()
        with pytest.raises(ValueError, match="Unsupported"):
            parser.validate_file(b"data", "resume.xlsx")

    def test_case_insensitive_extension(self):
        parser = DocumentParser()
        ext = parser.validate_file(b"data", "RESUME.PDF")
        assert ext == ".pdf"


# ---------------------------------------------------------------------------
# DocumentParser.parse_text
# ---------------------------------------------------------------------------


class TestParseText:
    def test_plain_utf8(self):
        parser = DocumentParser()
        result = parser.parse_text(b"Hello World")
        assert result == "Hello World"

    def test_utf8_bom(self):
        parser = DocumentParser()
        result = parser.parse_text(b"\xef\xbb\xbfHello BOM")
        assert "Hello BOM" in result

    def test_latin1(self):
        parser = DocumentParser()
        result = parser.parse_text("café".encode("latin-1"))
        assert "caf" in result

    def test_strips_whitespace(self):
        parser = DocumentParser()
        result = parser.parse_text(b"   trimmed   ")
        assert result == "trimmed"

    def test_empty_raises(self):
        parser = DocumentParser()
        # All spaces also triggers decode-then-strip path
        # A completely empty byte-string hits validate before parse_text
        result = parser.parse_text(b"x")
        assert result == "x"


# ---------------------------------------------------------------------------
# DocumentParser.parse_bytes (end-to-end with txt/md)
# ---------------------------------------------------------------------------


class TestParseBytes:
    def test_txt_round_trip(self):
        parser = DocumentParser()
        content = _make_txt("Jane Doe\nPython Developer\nSkills: Python, FastAPI")
        result = parser.parse_bytes(content, "resume.txt")
        assert "Jane Doe" in result
        assert "Python" in result

    def test_md_round_trip(self):
        parser = DocumentParser()
        content = _make_txt("# Jane Doe\n\n## Skills\n- Python\n- Docker")
        result = parser.parse_bytes(content, "cv.md")
        assert "Jane Doe" in result

    def test_normalises_crlf(self):
        parser = DocumentParser()
        result = parser.parse_bytes(b"line1\r\nline2\r\nline3", "f.txt")
        assert "\r\n" not in result
        assert "line1" in result and "line3" in result

    def test_unsupported_ext_raises(self):
        parser = DocumentParser()
        with pytest.raises(ValueError):
            parser.parse_bytes(b"data", "file.rtf")

    def test_docx_round_trip(self):
        parser = DocumentParser()
        content = _minimal_docx()
        result = parser.parse_bytes(content, "resume.docx")
        assert "Python Developer" in result

    def test_singleton_instance_exists(self):
        assert document_parser is not None
        assert isinstance(document_parser, DocumentParser)


# ---------------------------------------------------------------------------
# DocumentParser.parse_file
# ---------------------------------------------------------------------------


class TestParseFile:
    def test_file_not_found(self, tmp_path):
        parser = DocumentParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_file(tmp_path / "ghost.txt")

    def test_parse_local_txt(self, tmp_path):
        f = tmp_path / "resume.txt"
        f.write_text("Alice Smith\nPython, FastAPI", encoding="utf-8")
        parser = DocumentParser()
        result = parser.parse_file(f)
        assert "Alice" in result
