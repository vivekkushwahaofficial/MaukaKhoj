from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoreDimension:
    """Score contribution for one scoring dimension."""

    score: float
    max_score: float
    evidence: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class JobScore:
    """Deterministic 0-100 score for a job."""

    total: float
    role: ScoreDimension
    skills: ScoreDimension
    experience: ScoreDimension
    location: ScoreDimension
    freshness: ScoreDimension
    employment: ScoreDimension
    explanation: tuple[str, ...] = field(default_factory=tuple)