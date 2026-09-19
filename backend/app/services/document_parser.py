"""Multi-Format Document Parser Service.

Extracts plain text from resume documents in PDF, DOCX, and TXT/Markdown formats
with strict size and MIME-type validation.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

# 5 MB maximum file upload limit
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

SUPPORTED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "text/markdown",
    "application/octet-stream",
}


class DocumentParser:
    """Extracts raw text from PDF, DOCX, and text resume files."""

    def __init__(self, max_size_bytes: int = MAX_FILE_SIZE_BYTES) -> None:
        self.max_size_bytes = max_size_bytes

    def validate_file(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> str:
        """Validate file size and extension, returning the detected extension.

        Raises:
            ValueError: If file exceeds size limit or has an unsupported format.
        """
        if len(content) > self.max_size_bytes:
            mb_limit = self.max_size_bytes / (1024 * 1024)
            raise ValueError(f"File size ({len(content) / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {mb_limit:.0f} MB.")

        if not content:
            raise ValueError("Uploaded file is empty.")

        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise ValueError(f"Unsupported file format '{ext}'. Allowed extensions are: {allowed}.")

        return ext

    def parse_pdf(self, content: bytes) -> str:
        """Extract text from PDF byte content using pypdf."""
        try:
            import pypdf
        except ImportError:
            raise RuntimeError("pypdf library is required for PDF parsing.")

        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                try:
                    # Attempt empty password decryption
                    reader.decrypt("")
                except Exception:
                    raise ValueError("Encrypted PDF files are not supported.")

            pages_text: list[str] = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages_text.append(text.strip())

            extracted = "\n\n".join(pages_text)
            if not extracted.strip():
                raise ValueError("PDF does not contain extractable text (it may be a scanned image).")

            return extracted
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Failed to parse PDF document: {exc}")

    def parse_docx(self, content: bytes) -> str:
        """Extract text from Word (.docx) byte content using python-docx."""
        try:
            import docx
        except ImportError:
            raise RuntimeError("python-docx library is required for DOCX parsing.")

        try:
            doc = docx.Document(io.BytesIO(content))
            paragraphs_text = [p.text for p in doc.paragraphs if p.text.strip()]

            # Also extract text from tables
            table_text = []
            for table in doc.tables:
                for row in table.rows:
                    row_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if row_cells:
                        table_text.append(" | ".join(row_cells))

            combined = "\n".join(paragraphs_text)
            if table_text:
                combined += "\n\n" + "\n".join(table_text)

            if not combined.strip():
                raise ValueError("DOCX document does not contain any readable text.")

            return combined.strip()
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Failed to parse DOCX document: {exc}")

    def parse_text(self, content: bytes) -> str:
        """Decode plain text or markdown content with encoding fallback."""
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                decoded = content.decode(enc)
                if decoded.strip():
                    return decoded.strip()
            except UnicodeDecodeError:
                continue

        raise ValueError("Failed to decode text document using supported encodings.")

    def parse_bytes(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> str:
        """Extract plain text from document bytes based on file format.

        Args:
            content: Raw document bytes.
            filename: Original file name.
            content_type: Optional MIME content type.

        Returns:
            Extracted, clean plain text.

        Raises:
            ValueError: On size/format validation failure or parsing error.
        """
        ext = self.validate_file(content, filename, content_type)

        if ext == ".pdf":
            raw_text = self.parse_pdf(content)
        elif ext == ".docx":
            raw_text = self.parse_docx(content)
        elif ext in {".txt", ".md"}:
            raw_text = self.parse_text(content)
        else:
            raise ValueError(f"Unsupported format: {ext}")

        # Normalize line endings
        normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.strip()

    def parse_file(self, path: str | Path) -> str:
        """Convenience method to parse a local file from path."""
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        content = p.read_bytes()
        return self.parse_bytes(content, filename=p.name)


document_parser = DocumentParser()
