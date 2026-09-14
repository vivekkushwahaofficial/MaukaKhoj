from dataclasses import dataclass, field
from enum import Enum

from app.domain.job import Job


class DuplicateReason(str, Enum):
    """Reason why two jobs were considered duplicates."""

    SAME_SOURCE_JOB_ID = "SAME_SOURCE_JOB_ID"
    SAME_APPLICATION_URL = "SAME_APPLICATION_URL"
    SAME_SOURCE_URL = "SAME_SOURCE_URL"


@dataclass(frozen=True)
class DuplicateRecord:
    """Record describing a removed duplicate job."""

    duplicate_job: Job
    kept_job: Job
    reason: DuplicateReason


@dataclass(frozen=True)
class DeduplicationResult:
    """Result of deduplicating a collection of jobs."""

    unique_jobs: tuple[Job, ...] = field(default_factory=tuple)
    duplicates: tuple[DuplicateRecord, ...] = field(default_factory=tuple)
