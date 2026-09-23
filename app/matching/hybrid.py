from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.semantic.models import SemanticJobAnalysis
from app.matching.models import MatchResult


@dataclass(frozen=True)
class HybridMatchEvidence:
    """Combined deterministic and semantic evidence for one job."""

    deterministic: MatchResult
    semantic: SemanticJobAnalysis | None = None
    semantic_role_match: bool | None = None
    semantic_skill_matches: tuple[str, ...] = field(default_factory=tuple)
    semantic_domain_matches: tuple[str, ...] = field(default_factory=tuple)
    semantic_evidence: tuple[str, ...] = field(default_factory=tuple)
