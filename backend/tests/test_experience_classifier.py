"""Unit tests for the ExperienceClassifier service."""

import pytest

from app.schemas.enums import ExperienceLevel
from app.services.experience_classifier import ExperienceClassifier, experience_classifier


class TestExperienceClassifier:
    """Test suite for seniority classification and years-of-experience extraction."""

    @pytest.mark.parametrize(
        ("title", "expected_level"),
        [
            ("Junior Software Engineer", ExperienceLevel.ENTRY),
            ("Entry Level Python Developer", ExperienceLevel.ENTRY),
            ("Software Engineering Intern", ExperienceLevel.ENTRY),
            ("Senior Backend Engineer", ExperienceLevel.SENIOR),
            ("Sr. Cloud Architect", ExperienceLevel.LEAD),
            ("Principal Systems Engineer", ExperienceLevel.LEAD),
            ("Engineering Lead", ExperienceLevel.LEAD),
            ("Software Engineer", ExperienceLevel.MID),
        ],
    )
    def test_classify_by_title(self, title: str, expected_level: ExperienceLevel) -> None:
        res = experience_classifier.classify(title=title)
        assert res.level == expected_level

    def test_classify_by_years_in_requirements(self) -> None:
        title = "Full Stack Engineer"  # Generic title
        reqs = "Requirements: Must have 6+ years of experience building web systems."

        res = experience_classifier.classify(title=title, requirements=reqs)
        assert res.level == ExperienceLevel.SENIOR
        assert res.detected_years == 6

    def test_classify_entry_level_by_years(self) -> None:
        title = "Python Developer"
        reqs = "1 year of experience with Python and Git."

        res = experience_classifier.classify(title=title, requirements=reqs)
        assert res.level == ExperienceLevel.ENTRY
        assert res.detected_years == 1

    def test_extract_years_variations(self) -> None:
        assert experience_classifier.extract_years_requirement("3-5 years of experience") == 3
        assert experience_classifier.extract_years_requirement("8+ yrs exp") == 8
        assert experience_classifier.extract_years_requirement("No minimum requirement") is None
