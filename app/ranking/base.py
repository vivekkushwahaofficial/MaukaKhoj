from abc import ABC, abstractmethod

from app.domain.job import Job
from app.ranking.models import RankedJob, RankingResult
from app.scoring.models import JobScore


class JobRanker(ABC):
    """Base contract for ranking scored canonical jobs."""

    @abstractmethod
    def rank(
        self,
        scored_jobs: list[tuple[Job, JobScore]],
        limit: int | None = None,
    ) -> RankingResult:
        """Rank scored jobs and optionally select the top jobs."""

        raise NotImplementedError
