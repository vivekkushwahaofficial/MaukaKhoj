from datetime import datetime, timezone
from typing import Any

from app.domain.job import Job, RemoteType
from app.filtering.base import JobHardFilter
from app.filtering.models import FilterResult, RejectedJob, RejectionReason


class CanonicalJobHardFilter(JobHardFilter):
    """Apply profile-independent hard eligibility rules."""

    def __init__(
        self,
        *,
        freshness_config: dict[str, Any] | None = None,
    ) -> None:
        config = freshness_config or {}

        self._freshness_enabled = bool(
            config.get("enabled", False),
        )
        self._max_age_days = self._parse_max_age_days(
            config.get("max_age_days", 30),
        )

    def filter(
        self,
        jobs: list[Job],
    ) -> FilterResult:
        eligible_jobs: list[Job] = []
        rejected_jobs: list[RejectedJob] = []

        for job in jobs:
            reason = self._get_rejection_reason(job)

            if reason is None:
                eligible_jobs.append(job)
                continue

            rejected_jobs.append(
                RejectedJob(
                    job=job,
                    reason=reason,
                )
            )

        return FilterResult(
            eligible_jobs=tuple(eligible_jobs),
            rejected_jobs=tuple(rejected_jobs),
        )

    def _get_rejection_reason(
        self,
        job: Job,
    ) -> RejectionReason | None:
        if job.remote_type == RemoteType.ONSITE:
            return RejectionReason.ONSITE

        if job.remote_type == RemoteType.HYBRID:
            return RejectionReason.HYBRID

        if self._is_stale(job):
            return RejectionReason.STALE

        return None

    def _is_stale(self, job: Job) -> bool:
        """Return whether a job is older than the configured freshness window."""
        if not self._freshness_enabled:
            return False

        if job.posted_at is None:
            return False

        posted_at = job.posted_at

        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        else:
            posted_at = posted_at.astimezone(timezone.utc)

        now = datetime.now(timezone.utc)
        age_seconds = (now - posted_at).total_seconds()

        if age_seconds <= 0:
            return False

        return age_seconds > self._max_age_days * 24 * 60 * 60

    @staticmethod
    def _parse_max_age_days(value: Any) -> int:
        """Validate the configured maximum job age."""
        if isinstance(value, bool):
            raise ValueError("freshness.max_age_days must be a positive integer.")

        try:
            max_age_days = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "freshness.max_age_days must be a positive integer.",
            ) from exc

        if max_age_days <= 0:
            raise ValueError(
                "freshness.max_age_days must be a positive integer.",
            )

        return max_age_days
