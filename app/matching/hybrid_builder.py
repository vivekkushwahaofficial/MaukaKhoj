from __future__ import annotations

from app.ai.semantic.models import SemanticJobAnalysis
from app.domain.profile import Profile
from app.matching.hybrid import HybridMatchEvidence
from app.matching.models import MatchResult
from app.matching.job import CanonicalJobProfileMatcher


class HybridMatchEvidenceBuilder:
    """Combine deterministic matching with AI-derived semantic evidence."""

    def build(
        self,
        *,
        match_result: MatchResult,
        profile: Profile,
        semantic_analysis: SemanticJobAnalysis | None = None,
    ) -> HybridMatchEvidence:
        """Build hybrid evidence without modifying deterministic matching."""

        if semantic_analysis is None:
            return HybridMatchEvidence(
                deterministic=match_result,
            )

        profile_skills = {
            self._normalize(skill)
            for skill in profile.skills
        }

        semantic_skill_matches = tuple(
            skill
            for skill in semantic_analysis.semantic_skills
            if self._normalize(skill) in profile_skills
        )

        profile_domains = {
            self._normalize(domain)
            for domain in profile.domains
        }

        semantic_domain_matches = tuple(
            domain
            for domain in semantic_analysis.domains
            if self._normalize(domain) in profile_domains
        )

        semantic_role_match = self._role_family_matches(
            semantic_analysis,
            profile,
        )

        return HybridMatchEvidence(
            deterministic=match_result,
            semantic=semantic_analysis,
            semantic_role_match=semantic_role_match,
            semantic_skill_matches=semantic_skill_matches,
            semantic_domain_matches=semantic_domain_matches,
            semantic_evidence=semantic_analysis.evidence,
        )

    @classmethod
    def _role_family_matches(
        cls,
        analysis: SemanticJobAnalysis,
        profile: Profile,
    ) -> bool | None:
        if not analysis.role_family:
            return None

        configured_families = {
            CanonicalJobProfileMatcher.role_family_for_target(target)
            for target in profile.target_titles
        }

        configured_families.discard(None)

        return cls._normalize(analysis.role_family) in {
            cls._normalize(family)
            for family in configured_families
        }

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.lower().strip().split())
