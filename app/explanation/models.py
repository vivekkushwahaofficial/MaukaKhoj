from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExplanationDimension:
    """Human-readable explanation for one matching dimension."""

    dimension: str
    status: str
    reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class JobExplanation:
    """Deterministic explanation of why a job matches a profile."""

    dimensions: tuple[ExplanationDimension, ...] = field(default_factory=tuple)
    summary: tuple[str, ...] = field(default_factory=tuple)
