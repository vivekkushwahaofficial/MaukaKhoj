from abc import ABC, abstractmethod

from app.domain.job import Job
from app.filtering.models import FilterResult


class JobHardFilter(ABC):
    """Base contract for hard-filtering canonical jobs."""

    @abstractmethod
    def filter(
        self,
        jobs: list[Job],
    ) -> FilterResult:
        """Return eligible and rejected jobs."""

        raise NotImplementedError
