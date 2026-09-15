"""Unit tests for the BoundaryMatcher ambiguous term disambiguation service."""

import pytest

from app.services.extractor.boundary_matcher import BoundaryMatcher, boundary_matcher


class TestBoundaryMatcher:
    """Test suite for disambiguating Go, C, R, and short programming acronyms."""

    def test_go_positive_matches(self) -> None:
        text1 = "Seeking a Senior Go Developer for backend APIs."
        span1 = (text1.index("Go"), text1.index("Go") + 2)
        assert boundary_matcher.is_go_programming_match(text1, span1) is True

        text2 = "Proficient in Python, Java, Go, and Rust."
        span2 = (text2.index("Go"), text2.index("Go") + 2)
        assert boundary_matcher.is_go_programming_match(text2, span2) is True

        text3 = "Microservices written in Go."
        span3 = (text3.index("Go"), text3.index("Go") + 2)
        assert boundary_matcher.is_go_programming_match(text3, span3) is True

    def test_go_negative_suppression(self) -> None:
        text1 = "We like candidates who go above and beyond."
        span1 = (text1.index("go"), text1.index("go") + 2)
        assert boundary_matcher.is_go_programming_match(text1, span1) is False

        text2 = "This is our go-to solution for customers on the go."
        span2 = (text2.index("go"), text2.index("go") + 2)
        assert boundary_matcher.is_go_programming_match(text2, span2) is False

    def test_c_positive_and_negative(self) -> None:
        text1 = "Experience in C/C++ and Linux kernel internals."
        span1 = (text1.index("C"), text1.index("C") + 1)
        assert boundary_matcher.is_c_programming_match(text1, span1) is True

        text2 = "Looking for a C-level executive to lead the team."
        span2 = (text2.index("C"), text2.index("C") + 1)
        assert boundary_matcher.is_c_programming_match(text2, span2) is False

    def test_r_positive_and_negative(self) -> None:
        text1 = "Data analysis with Python and R for statistical modeling."
        span1 = (text1.index("R"), text1.index("R") + 1)
        assert boundary_matcher.is_r_programming_match(text1, span1) is True

        text2 = "Leading the R&D initiative on consumer hardware."
        span2 = (text2.index("R"), text2.index("R") + 1)
        assert boundary_matcher.is_r_programming_match(text2, span2) is False
