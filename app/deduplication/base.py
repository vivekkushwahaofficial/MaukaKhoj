from abc import ABC, abstractmethod

from app.domain.job import Job
from app.deduplication.models import DeduplicationResult


class JobDeduplicator(ABC):
    """Base contract for deduplicating canonical Jobs."""

    @abstractmethod
    def deduplicate(
        self,
        jobs: list[Job],
    ) -> DeduplicationResult:
        """Remove duplicate jobs while preserving unique jobs."""

        raise NotImplementedError
