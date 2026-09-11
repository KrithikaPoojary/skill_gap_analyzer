"""Job posting SQLAlchemy ORM model.

Stores scraped and synthesized job postings, metadata, employment terms,
salary bands, and raw requirements for skill extraction.
"""

from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, utc_now


class JobPosting(Base, TimestampMixin):
    """Job posting entity capturing job market listings and specifications."""

    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    employment_type: Mapped[str] = mapped_column(
        String(50),
        default="full-time",
        nullable=False,
    )  # full-time, part-time, contract, internship
    experience_level: Mapped[str] = mapped_column(
        String(50),
        default="mid",
        nullable=False,
    )  # entry, mid, senior, lead, executive
    min_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_platform: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    posted_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<JobPosting(id={self.id}, title='{self.title}', company='{self.company_name}')>"
