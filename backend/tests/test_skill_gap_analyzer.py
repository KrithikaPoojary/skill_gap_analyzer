"""Unit tests for the SkillGapAnalyzer service.

Covers gap score calculation, weighted scoring, critical blocker detection,
multi-role ranking, edge cases (empty profile, empty role, perfect match).
"""

from __future__ import annotations

import pytest

from app.services.skill_gap_analyzer import GapReport, SkillGapAnalyzer, SkillWeight

# Reusable test instance (stateless service)
analyzer = SkillGapAnalyzer()


class TestBasicGapAnalysis:
    """Core gap calculation correctness."""

    def test_perfect_match_score_is_one(self) -> None:
        profile = ["Python", "FastAPI", "PostgreSQL"]
        required = [
            SkillWeight("Python", 1.0),
            SkillWeight("FastAPI", 1.0),
            SkillWeight("PostgreSQL", 1.0),
        ]
        report = analyzer.analyse(
            profile_skills=profile, required_skills=required, role_name="Backend Dev"
        )
        assert report.gap_score == 1.0
        assert report.weighted_gap_score == 1.0
        assert report.coverage_pct == 100.0
        assert report.missing_skills == []
        assert set(report.matched_skills) == {"Python", "FastAPI", "PostgreSQL"}

    def test_zero_overlap_score_is_zero(self) -> None:
        profile = ["Photoshop", "Figma"]
        required = [SkillWeight("Python", 1.0), SkillWeight("Docker", 1.0)]
        report = analyzer.analyse(
            profile_skills=profile, required_skills=required, role_name="Engineer"
        )
        assert report.gap_score == 0.0
        assert report.weighted_gap_score == 0.0
        assert len(report.missing_skills) == 2

    def test_partial_match_computes_correctly(self) -> None:
        profile = ["Python", "Docker"]
        required = [
            SkillWeight("Python", 1.0),
            SkillWeight("Docker", 1.0),
            SkillWeight("Kubernetes", 1.0),
            SkillWeight("Terraform", 1.0),
        ]
        report = analyzer.analyse(profile_skills=profile, required_skills=required)
        assert report.gap_score == pytest.approx(0.5, abs=1e-4)
        assert len(report.matched_skills) == 2
        assert len(report.missing_skills) == 2

    def test_surplus_skills_identified(self) -> None:
        profile = ["Python", "Docker", "Photoshop", "Blender"]
        required = [SkillWeight("Python", 1.0), SkillWeight("Docker", 1.0)]
        report = analyzer.analyse(profile_skills=profile, required_skills=required)
        assert set(report.surplus_skills) == {"Photoshop", "Blender"}
        assert report.gap_score == 1.0  # all required skills covered


class TestWeightedGapScore:
    """Weighted scoring reflects skill importance."""

    def test_weighted_score_differs_from_unweighted(self) -> None:
        profile = ["Python"]  # only the low-weight skill present
        required = [
            SkillWeight("Python", 0.2),  # nice-to-have
            SkillWeight("Kubernetes", 1.0),  # mandatory
        ]
        report = analyzer.analyse(profile_skills=profile, required_skills=required)
        # unweighted: 1/2 = 0.5, weighted: 0.2/1.2 ≈ 0.167
        assert report.gap_score == pytest.approx(0.5, abs=1e-4)
        assert report.weighted_gap_score == pytest.approx(0.2 / 1.2, abs=1e-4)
        assert report.weighted_gap_score < report.gap_score

    def test_missing_skills_sorted_by_weight_descending(self) -> None:
        profile: list[str] = []
        required = [
            SkillWeight("Terraform", 0.3),
            SkillWeight("Kubernetes", 1.0),
            SkillWeight("Docker", 0.7),
        ]
        report = analyzer.analyse(profile_skills=profile, required_skills=required)
        weights = [sw.weight for sw in report.missing_skills]
        assert weights == sorted(weights, reverse=True)


class TestCriticalBlockers:
    """Skills with weight > 0.8 that are missing should appear in missing_critical."""

    def test_critical_skills_flagged(self) -> None:
        profile = ["Python"]
        required = [
            SkillWeight("Python", 1.0),
            SkillWeight("Docker", 0.9),   # critical and missing
            SkillWeight("Ansible", 0.5),  # not critical
        ]
        report = analyzer.analyse(profile_skills=profile, required_skills=required)
        assert "Docker" in report.missing_critical
        assert "Ansible" not in report.missing_critical

    def test_no_critical_missing_when_all_present(self) -> None:
        profile = ["Python", "Docker"]
        required = [SkillWeight("Python", 1.0), SkillWeight("Docker", 0.9)]
        report = analyzer.analyse(profile_skills=profile, required_skills=required)
        assert report.missing_critical == []


class TestCaseInsensitiveMatching:
    """Matching must be case-insensitive."""

    def test_case_variants_match(self) -> None:
        profile = ["python", "DOCKER", "React"]
        required = [
            SkillWeight("Python", 1.0),
            SkillWeight("Docker", 1.0),
            SkillWeight("react", 1.0),
        ]
        report = analyzer.analyse(profile_skills=profile, required_skills=required)
        assert report.gap_score == 1.0
        assert report.missing_skills == []


class TestEdgeCases:
    """Edge cases: empty profile, empty role, empty both."""

    def test_empty_profile_all_skills_missing(self) -> None:
        required = [SkillWeight("Python", 1.0), SkillWeight("AWS", 0.8)]
        report = analyzer.analyse(profile_skills=[], required_skills=required)
        assert report.gap_score == 0.0
        assert len(report.missing_skills) == 2
        assert report.matched_skills == []

    def test_empty_required_returns_perfect_score(self) -> None:
        report = analyzer.analyse(
            profile_skills=["Python", "Docker"],
            required_skills=[],
            role_name="Open Role",
        )
        assert report.gap_score == 1.0
        assert report.weighted_gap_score == 1.0
        assert report.coverage_pct == 100.0

    def test_both_empty_returns_perfect_score(self) -> None:
        report = analyzer.analyse(profile_skills=[], required_skills=[])
        assert report.gap_score == 1.0

    def test_to_dict_serialisable(self) -> None:
        profile = ["Python", "Docker"]
        required = [SkillWeight("Python", 1.0), SkillWeight("Kubernetes", 0.9)]
        report = analyzer.analyse(profile_skills=profile, required_skills=required)
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "gap_score" in d
        assert "matched_skills" in d
        assert "missing_skills" in d
        assert isinstance(d["missing_skills"], list)
        if d["missing_skills"]:
            assert "name" in d["missing_skills"][0]
            assert "weight" in d["missing_skills"][0]


class TestMultiRoleAnalysis:
    """analyse_multi ranks roles by best fit."""

    def test_best_fit_role_ranked_first(self) -> None:
        profile = ["Python", "FastAPI", "PostgreSQL"]
        roles = {
            "Backend Dev": [
                SkillWeight("Python", 1.0),
                SkillWeight("FastAPI", 1.0),
                SkillWeight("PostgreSQL", 1.0),
            ],
            "Data Scientist": [
                SkillWeight("Python", 1.0),
                SkillWeight("TensorFlow", 1.0),
                SkillWeight("Pandas", 1.0),
            ],
            "DevOps Engineer": [
                SkillWeight("Docker", 1.0),
                SkillWeight("Kubernetes", 1.0),
                SkillWeight("Terraform", 1.0),
            ],
        }
        reports = analyzer.analyse_multi(profile_skills=profile, roles=roles)
        assert len(reports) == 3
        # Backend Dev should be ranked first (full match)
        assert reports[0].role_name == "Backend Dev"
        assert reports[0].weighted_gap_score == pytest.approx(1.0)

    def test_worst_fit_role_ranked_last(self) -> None:
        profile = ["Python", "FastAPI"]
        roles = {
            "A": [SkillWeight("Python", 1.0)],
            "B": [SkillWeight("Java", 1.0), SkillWeight("Spring Boot", 1.0)],
        }
        reports = analyzer.analyse_multi(profile_skills=profile, roles=roles)
        assert reports[-1].role_name == "B"
