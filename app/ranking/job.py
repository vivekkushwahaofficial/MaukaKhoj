from datetime import datetime, timezone

from app.domain.job import Job
from app.ranking.base import JobRanker
from app.ranking.models import RankedJob, RankingResult
from app.scoring.models import JobScore


class DeterministicJobRanker(JobRanker):
    """Rank scored jobs using deterministic, explainable tie-breakers."""

    def rank(
        self,
        scored_jobs: list[tuple[Job, JobScore]],
        limit: int | None = None,
    ) -> RankingResult:
        if limit is not None and limit < 0:
            raise ValueError("Ranking limit cannot be negative.")

        sorted_jobs = sorted(
            scored_jobs,
            key=self._sort_key,
        )

        ranked_jobs = tuple(
            RankedJob(
                job=job,
                score=score,
                rank=index,
            )
            for index, (job, score) in enumerate(sorted_jobs, start=1)
        )

        selected_jobs = (
            ranked_jobs
            if limit is None
            else ranked_jobs[:limit]
        )

        return RankingResult(
            ranked_jobs=ranked_jobs,
            selected_jobs=selected_jobs,
        )

    @staticmethod
    def _sort_key(
        scored_job: tuple[Job, JobScore],
    ) -> tuple[float, float, str, str, str]:
        job, score = scored_job

        posted_timestamp = (
            DeterministicJobRanker._posted_timestamp(job.posted_at)
        )

        return (
            -score.total,
            -posted_timestamp,
            job.company.casefold(),
            job.title.casefold(),
            job.job_id,
        )

    @staticmethod
    def _posted_timestamp(posted_at: datetime | None) -> float:
        """Convert posted_at into a comparable UTC timestamp."""

        if posted_at is None:
            return float("-inf")

        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        else:
            posted_at = posted_at.astimezone(timezone.utc)

        return posted_at.timestamp()