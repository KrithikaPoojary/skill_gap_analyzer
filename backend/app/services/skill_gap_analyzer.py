"""SkillGapAnalyzer — Core skill-gap computation service.

Given a list of skills extracted from a resume/profile and a target role's
required skill set (sourced from the market analytics data), this service
computes:
  - matched skills (present in profile AND required by role)
  - missing skills (required by role but absent from profile)
  - surplus skills (in profile but not required by the role)
  - a numeric gap score in [0.0, 1.0]  (1.0 = perfect match, 0.0 = no overlap)
  - a weighted gap score that factors in each skill's importance weighting

The service is pure-computation (no DB access) so it is fast, fully testable,
and suitable for embedding inside both the REST API and the CLI demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────────────
# Data transfer objects
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SkillWeight:
    """A role-required skill annotated with an importance weighting [0.0, 1.0]."""

    name: str
    weight: float = 1.0  # 1.0 = mandatory, lower = nice-to-have


@dataclass
class GapReport:
    """Full gap analysis between a candidate profile and a target role.

    Attributes:
        role_name:       Human-readable label for the target role.
        matched_skills:  Skills present in profile AND required by role.
        missing_skills:  Skills required by role but NOT in profile (with weights).
        surplus_skills:  Skills in profile that aren't required by the role.
        gap_score:       Unweighted overlap ratio  (matched / required).
        weighted_gap_score: Weighted score (accounts for skill importance).
        coverage_pct:    Percentage of required skills already covered.
        missing_critical: Missing skills with weight > 0.8 (blockers).
    """

    role_name: str
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[SkillWeight] = field(default_factory=list)
    surplus_skills: list[str] = field(default_factory=list)
    gap_score: float = 0.0
    weighted_gap_score: float = 0.0
    coverage_pct: float = 0.0
    missing_critical: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "role_name": self.role_name,
            "gap_score": round(self.gap_score, 4),
            "weighted_gap_score": round(self.weighted_gap_score, 4),
            "coverage_pct": round(self.coverage_pct, 2),
            "matched_skills": self.matched_skills,
            "missing_skills": [
                {"name": sw.name, "weight": round(sw.weight, 3)}
                for sw in self.missing_skills
            ],
            "surplus_skills": self.surplus_skills,
            "missing_critical": self.missing_critical,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Core service
# ─────────────────────────────────────────────────────────────────────────────


class SkillGapAnalyzer:
    """Stateless service that computes a gap report between profile and role skills."""

    # Normalisation helper ─────────────────────────────────────────────────

    @staticmethod
    def _normalise(name: str) -> str:
        """Lowercase + strip for case-insensitive matching."""
        return name.strip().lower()

    # Public API ───────────────────────────────────────────────────────────

    def analyse(
        self,
        *,
        profile_skills: list[str],
        required_skills: list[SkillWeight],
        role_name: str = "Target Role",
    ) -> GapReport:
        """Compute a GapReport comparing profile skills against role requirements.

        Args:
            profile_skills:   Skills extracted from a candidate's resume / profile.
            required_skills:  Weighted list of skills required by the target role.
            role_name:        Label for the target role (used in the report header).

        Returns:
            GapReport dataclass with all gap metrics populated.
        """
        if not required_skills:
            return GapReport(
                role_name=role_name,
                surplus_skills=sorted(profile_skills),
                gap_score=1.0,
                weighted_gap_score=1.0,
                coverage_pct=100.0,
            )

        profile_norm: set[str] = {self._normalise(s) for s in profile_skills}
        required_norm: dict[str, SkillWeight] = {
            self._normalise(sw.name): sw for sw in required_skills
        }

        matched_keys: set[str] = profile_norm & set(required_norm.keys())
        missing_keys: set[str] = set(required_norm.keys()) - matched_keys
        surplus_keys: set[str] = profile_norm - set(required_norm.keys())

        # Restore display names
        matched_display = sorted(required_norm[k].name for k in matched_keys)
        missing_display = sorted(
            [required_norm[k] for k in missing_keys],
            key=lambda sw: -sw.weight,  # highest weight first
        )
        surplus_display = sorted(
            next(
                (s for s in profile_skills if self._normalise(s) == k),
                k,
            )
            for k in surplus_keys
        )

        # Gap score (unweighted)
        n_required = len(required_skills)
        gap_score = len(matched_keys) / n_required

        # Weighted gap score
        total_weight = sum(sw.weight for sw in required_skills)
        matched_weight = sum(required_norm[k].weight for k in matched_keys)
        weighted_gap_score = matched_weight / total_weight if total_weight > 0 else 0.0

        coverage_pct = round(gap_score * 100, 2)

        missing_critical = [
            sw.name for sw in missing_display if sw.weight > 0.8
        ]

        return GapReport(
            role_name=role_name,
            matched_skills=matched_display,
            missing_skills=missing_display,
            surplus_skills=surplus_display,
            gap_score=round(gap_score, 4),
            weighted_gap_score=round(weighted_gap_score, 4),
            coverage_pct=coverage_pct,
            missing_critical=missing_critical,
        )

    def analyse_multi(
        self,
        *,
        profile_skills: list[str],
        roles: dict[str, list[SkillWeight]],
    ) -> list[GapReport]:
        """Analyse a profile against multiple roles at once.

        Args:
            profile_skills: Skills from the candidate profile.
            roles:          Dict mapping role_name -> list[SkillWeight].

        Returns:
            List of GapReports sorted by weighted_gap_score descending
            (best-fit roles first).
        """
        reports = [
            self.analyse(
                profile_skills=profile_skills,
                required_skills=skill_weights,
                role_name=role_name,
            )
            for role_name, skill_weights in roles.items()
        ]
        return sorted(reports, key=lambda r: r.weighted_gap_score, reverse=True)


# Module-level singleton
skill_gap_analyzer = SkillGapAnalyzer()
