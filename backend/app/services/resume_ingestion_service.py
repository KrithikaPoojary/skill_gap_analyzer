"""Resume Ingestion Service.

Orchestrates the full resume pipeline:
  1. Parse raw bytes with DocumentParser.
  2. Segment sections with ResumeSegmenter.
  3. Resolve extracted skills against the skill taxonomy.
  4. Persist new user–skill associations via UserSkillService.
  5. Update the user's Profile with contact metadata.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.schemas.resume import (
    ContactInfoSchema,
    ResumeIngestResponse,
    ResumeParseResponse,
)
from app.services.document_parser import DocumentParser, document_parser
from app.services.resume_segmenter import ResumeSegmenter, resume_segmenter
from app.services.skill_normalizer import skill_normalizer
from app.services.user_skill_service import user_skill_service
from app.services.profile_service import profile_service

logger = logging.getLogger(__name__)


class ResumeIngestionService:
    """Orchestrates document parsing, section segmentation, and profile ingestion."""

    def __init__(
        self,
        parser: DocumentParser | None = None,
        segmenter: ResumeSegmenter | None = None,
    ) -> None:
        self._parser = parser or document_parser
        self._segmenter = segmenter or resume_segmenter

    # ------------------------------------------------------------------
    # Parse-only (no DB writes)
    # ------------------------------------------------------------------

    def parse_only(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> ResumeParseResponse:
        """Extract and segment a resume without touching the database.

        Args:
            content: Raw file bytes.
            filename: Original filename (used for format detection).
            content_type: Optional MIME type hint.

        Returns:
            :class:`ResumeParseResponse` containing sections, contact info,
            and raw skill tokens.

        Raises:
            ValueError: On parse or validation failure.
        """
        text = self._parser.parse_bytes(content, filename, content_type)
        segments = self._segmenter.segment(text)

        contact_schema = ContactInfoSchema(
            name=segments.contact.name,
            email=segments.contact.email,
            phone=segments.contact.phone,
            linkedin_url=segments.contact.linkedin_url,
            github_url=segments.contact.github_url,
            website_url=segments.contact.website_url,
            location=segments.contact.location,
        )

        return ResumeParseResponse(
            filename=filename,
            file_size_bytes=len(content),
            char_count=len(text),
            sections_found=list(segments.sections.keys()),
            contact=contact_schema,
            skills_raw=segments.skills_raw,
            raw_text_preview=text[:500],
        )

    # ------------------------------------------------------------------
    # Full ingestion pipeline (with DB writes)
    # ------------------------------------------------------------------

    def ingest(
        self,
        db: Session,
        content: bytes,
        filename: str,
        user_id: int,
        content_type: Optional[str] = None,
    ) -> ResumeIngestResponse:
        """Parse, segment, and persist resume data for a user.

        Args:
            db: Active SQLAlchemy database session.
            content: Raw file bytes.
            filename: Original filename.
            user_id: Target user ID to associate skills and contact info with.
            content_type: Optional MIME type hint.

        Returns:
            :class:`ResumeIngestResponse` with counts of matched / added skills.

        Raises:
            ValueError: On parse, validation, or user-not-found failure.
        """
        # Step 1 & 2: Parse + segment
        parse_result = self.parse_only(content, filename, content_type)
        text = self._parser.parse_bytes(content, filename, content_type)
        segments = self._segmenter.segment(text)

        # Step 3: Resolve skills against taxonomy
        skills_matched = 0
        skills_added = 0
        for raw_skill in segments.skills_raw:
            try:
                skill_obj = skill_normalizer.resolve_or_create(db, raw_skill)
                skills_matched += 1

                # Check if association already exists before upserting
                from sqlalchemy import select
                from app.models.associations import UserSkill as _UserSkill
                existing = db.scalar(
                    select(_UserSkill).where(
                        _UserSkill.user_id == user_id,
                        _UserSkill.skill_id == skill_obj.id,
                    )
                )
                user_skill_service.add_user_skill(
                    db,
                    user_id=user_id,
                    skill_id=skill_obj.id,
                )
                if not existing:
                    skills_added += 1
            except Exception as exc:
                logger.warning("Skipping unresolvable skill '%s': %s", raw_skill, exc)

        # Step 4: Update profile with contact info
        profile_updated = False
        contact = segments.contact
        try:
            update_kwargs: dict[str, object] = {}
            if contact.linkedin_url:
                update_kwargs["linkedin_url"] = contact.linkedin_url
            if contact.github_url:
                update_kwargs["github_url"] = contact.github_url
            if contact.location:
                update_kwargs["location"] = contact.location

            if update_kwargs:
                profile_service.upsert_profile(db, user_id=user_id, **update_kwargs)  # type: ignore[arg-type]
                profile_updated = True
        except Exception as exc:
            logger.warning("Could not update profile for user %d: %s", user_id, exc)

        message = (
            f"Parsed {parse_result.char_count} chars; "
            f"{skills_matched} skills matched, {skills_added} added."
        )

        return ResumeIngestResponse(
            user_id=user_id,
            filename=filename,
            file_size_bytes=parse_result.file_size_bytes,
            char_count=parse_result.char_count,
            sections_found=parse_result.sections_found,
            contact=parse_result.contact,
            skills_raw=parse_result.skills_raw,
            skills_matched=skills_matched,
            skills_added=skills_added,
            profile_updated=profile_updated,
            message=message,
        )


resume_ingestion_service = ResumeIngestionService()
