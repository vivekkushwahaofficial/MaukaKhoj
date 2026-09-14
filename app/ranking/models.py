from dataclasses import dataclass, field

from app.domain.job import Job
from app.scoring.models import JobScore


@dataclass(frozen=True)
class RankedJob:
    """A canonical job together with its deterministic score."""

    job: Job
    score: JobScore
    rank: int


@dataclass(frozen=True)
class RankingResult:
    """Result of ranking and selecting scored jobs."""

    ranked_jobs: tuple[RankedJob, ...] = field(default_factory=tuple)
    selected_jobs: tuple[RankedJob, ...] = field(default_factory=tuple)
