"""Job domain enumerations and standard categorization constants."""

from enum import Enum


class EmploymentType(str, Enum):
    """Work arrangement and employment commitment types."""

    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class ExperienceLevel(str, Enum):
    """Seniority and required career stage levels."""

    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class Currency(str, Enum):
    """Supported salary compensation currency codes."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    CAD = "CAD"
    AUD = "AUD"


class SourcePlatform(str, Enum):
    """Origin platform or pipeline source for job market data."""

    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    MONSTER = "monster"
    MANUAL = "manual"
    SCRAPED = "scraped"
