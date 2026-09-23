from __future__ import annotations

import re

from app.ai.semantic.models import SemanticJobAnalysis
from app.domain.job import Job
from app.domain.profile import Profile
from app.matching.job import CanonicalJobProfileMatcher
from app.matching.models import MatchResult


class SemanticRelevanceGate:
    """Evaluate whether semantic evidence can rescue core role relevance."""

    _SENIORITY_EXCLUDE_PATTERN = re.compile(
        r"\b("
        r"senior|"
        r"sr\.?|"
        r"staff|"
        r"principal|"
        r"distinguished|"
        r"fellow|"
        r"lead|"
        r"tech\s+lead|"
        r"team\s+lead|"
        r"architect|"
        r"manager|"
        r"management|"
        r"director|"
        r"vp|"
        r"vice\s+president|"
        r"head\s+of|"
        r"chief|"
        r"cto"
        r")\b",
        re.IGNORECASE,
    )

    _SEMANTIC_SENIORITY = {
        "senior",
        "staff",
        "principal",
        "lead",
        "manager",
        "director",
        "executive",
        "chief",
    }

    def allows_core_profile(
        self,
        *,
        job: Job,
        match_result: MatchResult,
        profile: Profile,
        semantic_analysis: SemanticJobAnalysis | None = None,
    ) -> bool:
        """Return whether the job passes the core-profile relevance gate."""

        if self._is_senior_or_management_title(job.title):
            return False

        if not profile.target_titles:
            return (
                match_result.skills.matched is True
                or match_result.domain.matched is True
            )

        if match_result.role.matched is True:
            return True

        return self._semantic_role_match(
            semantic_analysis,
            profile,
        )

    def _semantic_role_match(
        self,
        analysis: SemanticJobAnalysis | None,
        profile: Profile,
    ) -> bool:
        if analysis is None:
            return False

        if analysis.seniority:
            seniority = analysis.seniority.strip().lower()
            if seniority in self._SEMANTIC_SENIORITY:
                return False

        role_family = (analysis.role_family or "").strip().lower()

        if not role_family:
            return False

        configured_families = {
            CanonicalJobProfileMatcher.role_family_for_target(target)
            for target in profile.target_titles
        }

        configured_families.discard(None)

        return role_family in configured_families

    @classmethod
    def _is_senior_or_management_title(cls, title: str) -> bool:
        """Return whether a job title contains an excluded seniority marker."""

        return bool(cls._SENIORITY_EXCLUDE_PATTERN.search(title))
