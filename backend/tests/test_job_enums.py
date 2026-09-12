"""Unit tests for job domain enumerations."""

import pytest

from app.schemas.enums import (
    Currency,
    EmploymentType,
    ExperienceLevel,
    SourcePlatform,
)


class TestJobEnums:
    """Test suite verifying enum values and string comparability."""

    def test_employment_type_values(self) -> None:
        assert EmploymentType.FULL_TIME == "full_time"
        assert EmploymentType.PART_TIME == "part_time"
        assert EmploymentType.CONTRACT == "contract"
        assert EmploymentType.INTERNSHIP == "internship"
        assert EmploymentType.FREELANCE == "freelance"

    def test_experience_level_values(self) -> None:
        assert ExperienceLevel.ENTRY == "entry"
        assert ExperienceLevel.MID == "mid"
        assert ExperienceLevel.SENIOR == "senior"
        assert ExperienceLevel.LEAD == "lead"
        assert ExperienceLevel.EXECUTIVE == "executive"

    def test_currency_values(self) -> None:
        assert Currency.USD == "USD"
        assert Currency.EUR == "EUR"
        assert Currency.INR == "INR"

    def test_source_platform_values(self) -> None:
        assert SourcePlatform.LINKEDIN == "linkedin"
        assert SourcePlatform.INDEED == "indeed"
        assert SourcePlatform.MANUAL == "manual"
        assert SourcePlatform.SCRAPED == "scraped"

    def test_enum_lookup_raises_on_invalid(self) -> None:
        with pytest.raises(ValueError):
            EmploymentType("nonexistent_type")

        with pytest.raises(ValueError):
            ExperienceLevel("intern_level")
