"""Resume ingestion API endpoints.

Provides multipart-upload endpoints for:
  - POST /resume/parse   – parse & segment only (no DB writes)
  - POST /resume/ingest  – full pipeline (parse + segment + skill + profile upsert)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.resume import ResumeIngestResponse, ResumeParseResponse
from app.services.resume_ingestion_service import resume_ingestion_service

router = APIRouter(prefix="/resume", tags=["Resume Ingestion"])

logger = logging.getLogger(__name__)

_MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


async def _read_upload(file: UploadFile) -> bytes:
    """Read and size-validate an uploaded file."""
    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds 5 MB limit ({len(content) / (1024 * 1024):.2f} MB uploaded).",
        )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    return content


@router.post(
    "/parse",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse and segment a resume document",
    description=(
        "Upload a PDF, DOCX, or TXT resume file. Returns extracted text sections, "
        "contact info, and raw skill tokens. **No database writes are performed.**"
    ),
)
async def parse_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT/MD)."),
) -> ResumeParseResponse:
    """Extract and segment a resume without persisting any data."""
    content = await _read_upload(file)
    filename = file.filename or "upload"
    content_type = file.content_type

    try:
        return resume_ingestion_service.parse_only(
            content=content,
            filename=filename,
            content_type=content_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during resume parsing.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while parsing the resume.",
        ) from exc


@router.post(
    "/ingest",
    response_model=ResumeIngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest a resume for a user (full pipeline)",
    description=(
        "Upload a resume for a specific user. Parses the document, segments sections, "
        "resolves skills against the taxonomy, and updates the user's profile with "
        "contact info. Skills are added to the user's profile as unverified associations."
    ),
)
async def ingest_resume(
    user_id: int = Form(..., ge=1, description="Target user ID."),
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT/MD)."),
    db: Session = Depends(get_db),
) -> ResumeIngestResponse:
    """Full resume ingestion pipeline with DB persistence."""
    content = await _read_upload(file)
    filename = file.filename or "upload"
    content_type = file.content_type

    try:
        return resume_ingestion_service.ingest(
            db=db,
            content=content,
            filename=filename,
            user_id=user_id,
            content_type=content_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during resume ingestion for user %d.", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while ingesting the resume.",
        ) from exc
