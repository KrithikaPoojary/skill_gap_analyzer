"""Unit tests for ResumeSegmenter service."""

from __future__ import annotations

import pytest

from app.services.resume_segmenter import (
    ContactInfo,
    ResumeSegments,
    ResumeSegmenter,
    resume_segmenter,
)


# ---------------------------------------------------------------------------
# Sample resume fixture
# ---------------------------------------------------------------------------

SAMPLE_RESUME = """John Smith
New York, NY
john.smith@example.com
+1 (555) 123-4567
https://linkedin.com/in/johnsmith
https://github.com/johnsmith

Summary
Experienced backend engineer with 5+ years in Python and cloud technologies.

Skills
Python, FastAPI, Docker, PostgreSQL, Redis, Kubernetes, AWS

Experience
Senior Software Engineer - Acme Corp (2020-Present)
- Built microservices using FastAPI and Docker
- Designed Kubernetes-based deployment pipelines

Education
B.Sc. Computer Science, State University, 2018

Certifications
AWS Certified Solutions Architect - Associate
"""

# ---------------------------------------------------------------------------
# Basic segmentation
# ---------------------------------------------------------------------------


class TestSegmentation:
    def setup_method(self):
        self.seg = ResumeSegmenter()

    def test_returns_resume_segments(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert isinstance(result, ResumeSegments)

    def test_raw_text_preserved(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert result.raw_text == SAMPLE_RESUME

    def test_sections_is_dict(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert isinstance(result.sections, dict)

    def test_skills_section_detected(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert "skills" in result.sections

    def test_experience_section_detected(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert "experience" in result.sections

    def test_education_section_detected(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert "education" in result.sections

    def test_certifications_section_detected(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert "certifications" in result.sections

    def test_summary_section_detected(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert "summary" in result.sections

    def test_header_captured(self):
        result = self.seg.segment(SAMPLE_RESUME)
        # Header lives in 'header' key (before any labelled section)
        assert "header" in result.sections

    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            self.seg.segment("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            self.seg.segment("   \n\n   ")


# ---------------------------------------------------------------------------
# Contact extraction
# ---------------------------------------------------------------------------


class TestContactExtraction:
    def setup_method(self):
        self.seg = ResumeSegmenter()

    def test_email_extracted(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert result.contact.email == "john.smith@example.com"

    def test_phone_extracted(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert result.contact.phone is not None
        assert "555" in result.contact.phone

    def test_linkedin_extracted(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert result.contact.linkedin_url is not None
        assert "linkedin.com" in result.contact.linkedin_url

    def test_github_extracted(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert result.contact.github_url is not None
        assert "github.com" in result.contact.github_url

    def test_name_extracted(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert result.contact.name == "John Smith"

    def test_location_extracted(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert result.contact.location is not None
        assert "New York" in result.contact.location

    def test_missing_contact_graceful(self):
        minimal = "Summary\nI am a developer.\n\nSkills\nPython"
        result = self.seg.segment(minimal)
        assert result.contact.email is None
        assert result.contact.phone is None

    def test_contact_info_is_dataclass(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert isinstance(result.contact, ContactInfo)


# ---------------------------------------------------------------------------
# Skills extraction
# ---------------------------------------------------------------------------


class TestSkillsExtraction:
    def setup_method(self):
        self.seg = ResumeSegmenter()

    def test_skills_list_populated(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert len(result.skills_raw) > 0

    def test_known_skill_present(self):
        result = self.seg.segment(SAMPLE_RESUME)
        assert "Python" in result.skills_raw

    def test_skills_deduped(self):
        resume = "Skills\nPython, Python, Docker\n"
        result = self.seg.segment(resume)
        counts = result.skills_raw.count("Python")
        assert counts == 1

    def test_no_skills_section_returns_empty(self):
        resume = "Summary\nI am a developer.\n"
        result = self.seg.segment(resume)
        assert result.skills_raw == []

    def test_bullet_point_skills(self):
        resume = "Skills\n- Python\n- Docker\n- Kubernetes\n"
        result = self.seg.segment(resume)
        assert "Python" in result.skills_raw
        assert "Docker" in result.skills_raw

    def test_pipe_separated_skills(self):
        resume = "Technical Skills\nPython | FastAPI | PostgreSQL | Redis\n"
        result = self.seg.segment(resume)
        assert len(result.skills_raw) >= 4


# ---------------------------------------------------------------------------
# Section heading variations
# ---------------------------------------------------------------------------


class TestSectionHeadingVariations:
    def setup_method(self):
        self.seg = ResumeSegmenter()

    def test_work_experience_heading(self):
        resume = "Work Experience\nWorked at Acme 2020-2022\n"
        result = self.seg.segment(resume)
        assert "experience" in result.sections

    def test_technical_skills_heading(self):
        resume = "Technical Skills\nPython, Go, Rust\n"
        result = self.seg.segment(resume)
        assert "skills" in result.sections

    def test_professional_summary_heading(self):
        resume = "Professional Summary\nSeasoned engineer...\n"
        result = self.seg.segment(resume)
        assert "summary" in result.sections

    def test_certifications_alias(self):
        resume = "Courses & Certifications\nAWS SAA\n"
        result = self.seg.segment(resume)
        assert "certifications" in result.sections

    def test_projects_section(self):
        resume = "Projects\nBuilt an open source library.\n"
        result = self.seg.segment(resume)
        assert "projects" in result.sections


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


def test_singleton_instance():
    assert resume_segmenter is not None
    assert isinstance(resume_segmenter, ResumeSegmenter)
