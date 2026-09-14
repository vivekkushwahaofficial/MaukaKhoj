from app.domain.job import Job, RemoteType
from app.filtering.base import JobHardFilter
from app.filtering.models import FilterResult, RejectedJob, RejectionReason


class CanonicalJobHardFilter(JobHardFilter):
    """Apply profile-independent hard eligibility rules."""

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

        return None
