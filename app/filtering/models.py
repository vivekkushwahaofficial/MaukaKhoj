from dataclasses import dataclass, field
from enum import Enum

from app.domain.job import Job


class RejectionReason(str, Enum):
    """Reason why a job was rejected by hard filters."""

    ONSITE = "ONSITE"
    HYBRID = "HYBRID"
    STALE = "STALE"


@dataclass(frozen=True)
class RejectedJob:
    """Record describing a job rejected by a hard filter."""

    job: Job
    reason: RejectionReason


@dataclass(frozen=True)
class FilterResult:
    """Result of applying hard filters to canonical jobs."""

    eligible_jobs: tuple[Job, ...] = field(default_factory=tuple)
    rejected_jobs: tuple[RejectedJob, ...] = field(default_factory=tuple)
