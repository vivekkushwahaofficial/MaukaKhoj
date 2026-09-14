from dataclasses import dataclass, field


@dataclass(frozen=True)
class MatchDimension:
    """Evidence for one profile-matching dimension."""

    matched: bool | None
    matched_values: tuple[str, ...] = field(default_factory=tuple)
    missing_values: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MatchResult:
    """Structured profile-matching evidence for a canonical job."""

    role: MatchDimension
    skills: MatchDimension
    experience: MatchDimension
    education: MatchDimension
    location: MatchDimension
    remote: MatchDimension
    employment: MatchDimension
    domain: MatchDimension
