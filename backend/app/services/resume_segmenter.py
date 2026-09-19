"""Resume Section Segmenter.

Splits raw resume text into structured sections (Contact, Summary,
Skills, Experience, Education, Certifications, Projects) using
heading-pattern heuristics and extracts contact metadata via regex.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Section heading patterns
# ---------------------------------------------------------------------------

_SECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("contact", re.compile(
        r"^\s*(?:contact(?:\s+(?:info(?:rmation)?|details?))?|personal\s+(?:info(?:rmation)?|details?))\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("summary", re.compile(
        r"^\s*(?:(?:professional\s+)?summary|objective|profile|about\s+me|career\s+objective)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("skills", re.compile(
        r"^\s*(?:(?:technical\s+)?skills?|core\s+competenc(?:ies|y)|technologies|tech(?:nical)?\s+stack|expertise|key\s+skills?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("experience", re.compile(
        r"^\s*(?:(?:work\s+|professional\s+)?experience|employment(?:\s+history)?|work\s+history|career\s+history|positions?\s+held)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("education", re.compile(
        r"^\s*(?:education(?:al\s+background)?|academic(?:\s+background)?|qualifications?|degrees?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("certifications", re.compile(
        r"^\s*(?:certifications?(?:\s+&\s+licenses?)?|licenses?|credentials?|professional\s+development|courses?(?:\s+&\s+certifications?)?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("projects", re.compile(
        r"^\s*(?:projects?|personal\s+projects?|open[\s-]?source|side\s+projects?|portfolio)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("awards", re.compile(
        r"^\s*(?:awards?(?:\s+&\s+honors?)?|honors?|achievements?|recognitions?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("languages", re.compile(
        r"^\s*(?:languages?|spoken\s+languages?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
    ("references", re.compile(
        r"^\s*(?:references?(?:\s+available\s+upon\s+request)?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )),
]

# ---------------------------------------------------------------------------
# Contact extraction patterns
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?"           # country code
    r"(?:\(?\d{2,4}\)?[\s.-]?)?"        # area code
    r"\d{3,4}[\s.-]?\d{3,4}"           # number body
    r"(?:\s*(?:ext|x)[\s.:]?\d{1,5})?",  # extension
    re.IGNORECASE,
)
_LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w%-]+/?", re.IGNORECASE)
_GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w.-]+/?", re.IGNORECASE)
_URL_RE = re.compile(r"https?://[\w/:%#$&?()~.=+\-]+", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class ContactInfo:
    """Extracted contact fields from resume text."""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None


@dataclass
class ResumeSegments:
    """Structured representation of a segmented resume."""

    raw_text: str
    sections: dict[str, str] = field(default_factory=dict)
    contact: ContactInfo = field(default_factory=ContactInfo)
    skills_raw: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Segmenter
# ---------------------------------------------------------------------------


class ResumeSegmenter:
    """Splits resume plain text into labelled sections and extracts contact info."""

    def segment(self, text: str) -> ResumeSegments:
        """Parse *text* into structured resume segments.

        Args:
            text: Raw, extracted plain text from a resume document.

        Returns:
            :class:`ResumeSegments` with populated sections and contact info.
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Resume text must be a non-empty string.")

        lines = text.splitlines()
        sections: dict[str, str] = {}
        current_section: str = "header"
        buffer: list[str] = []

        def _flush(section_name: str, buf: list[str]) -> None:
            content = "\n".join(buf).strip()
            if content:
                if section_name in sections:
                    sections[section_name] += "\n" + content
                else:
                    sections[section_name] = content

        for line in lines:
            matched_section: Optional[str] = None

            for section_label, pattern in _SECTION_PATTERNS:
                if pattern.match(line):
                    matched_section = section_label
                    break

            if matched_section is not None:
                _flush(current_section, buffer)
                buffer = []
                current_section = matched_section
            else:
                buffer.append(line)

        _flush(current_section, buffer)

        contact = self._extract_contact(sections.get("header", ""), text)
        skills_raw = self._extract_skills_list(sections.get("skills", ""))

        return ResumeSegments(
            raw_text=text,
            sections=sections,
            contact=contact,
            skills_raw=skills_raw,
        )

    # ------------------------------------------------------------------
    # Contact extraction helpers
    # ------------------------------------------------------------------

    def _extract_contact(self, header_text: str, full_text: str) -> ContactInfo:
        """Extract contact metadata preferring the header block, falling back
        to a full-document scan for any missing field."""
        search_text = header_text if header_text.strip() else full_text[:2000]

        email = self._first_match(_EMAIL_RE, search_text)
        phone = self._first_match_phone(search_text)
        linkedin = self._first_match(_LINKEDIN_RE, search_text)
        github = self._first_match(_GITHUB_RE, search_text)

        # Generic website (excluding already-captured linkedin/github)
        website: Optional[str] = None
        for url_match in _URL_RE.finditer(search_text):
            url = url_match.group(0)
            if "linkedin.com" not in url and "github.com" not in url:
                website = url
                break

        name = self._extract_name(header_text)
        location = self._extract_location(search_text)

        return ContactInfo(
            name=name,
            email=email,
            phone=phone,
            linkedin_url=linkedin,
            github_url=github,
            website_url=website,
            location=location,
        )

    def _first_match(self, pattern: re.Pattern[str], text: str) -> Optional[str]:
        m = pattern.search(text)
        return m.group(0) if m else None

    def _first_match_phone(self, text: str) -> Optional[str]:
        """Return the first plausible phone number (>= 7 digits)."""
        for m in _PHONE_RE.finditer(text):
            candidate = m.group(0).strip()
            digits = re.sub(r"\D", "", candidate)
            if len(digits) >= 7:
                return candidate
        return None

    def _extract_name(self, header_text: str) -> Optional[str]:
        """Heuristic: first non-empty line in the header that looks like a name
        (2-4 words, no digits, not a section keyword)."""
        if not header_text.strip():
            return None

        _SKIP_WORDS = {"resume", "cv", "curriculum", "vitae", "contact", "profile"}
        for line in header_text.splitlines():
            line = line.strip()
            if not line:
                continue
            words = line.split()
            if 2 <= len(words) <= 4:
                if not any(ch.isdigit() for ch in line):
                    if line.lower() not in _SKIP_WORDS:
                        if not re.search(r"[@|/\\<>{}]", line):
                            return line
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Heuristic: find patterns like 'City, State' or 'City, Country'."""
        loc_re = re.compile(
            r"\b([A-Z][a-zA-Z\s.-]{1,25}),\s*([A-Z]{2}|[A-Z][a-zA-Z\s]{2,20})\b"
        )
        m = loc_re.search(text)
        return m.group(0) if m else None

    # ------------------------------------------------------------------
    # Skills extraction helpers
    # ------------------------------------------------------------------

    def _extract_skills_list(self, skills_section: str) -> list[str]:
        """Parse a raw skills section into individual skill tokens."""
        if not skills_section.strip():
            return []

        skills: list[str] = []

        # Try comma / pipe / semicolon separated tokens first
        inline_pattern = re.compile(r"[,|;•·\t]")
        for line in skills_section.splitlines():
            line = line.strip()
            if not line:
                continue

            parts = inline_pattern.split(line)
            if len(parts) > 1:
                skills.extend(p.strip() for p in parts if p.strip())
            else:
                # Treat the whole line as one skill (bullet points etc.)
                clean = re.sub(r"^[-*•·]\s*", "", line)
                if clean:
                    skills.append(clean)

        # Deduplicate preserving order, skip very long "skills" (likely full sentences)
        seen: set[str] = set()
        result: list[str] = []
        for sk in skills:
            key = sk.lower()
            if key not in seen and len(sk) <= 60:
                seen.add(key)
                result.append(sk)

        return result


resume_segmenter = ResumeSegmenter()
