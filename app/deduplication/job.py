from app.deduplication.base import JobDeduplicator
from app.deduplication.models import (
    DuplicateReason,
    DuplicateRecord,
    DeduplicationResult,
)
from app.domain.job import Job


class CanonicalJobDeduplicator(JobDeduplicator):
    """Deduplicate canonical jobs using strong identity signals."""

    def deduplicate(
        self,
        jobs: list[Job],
    ) -> DeduplicationResult:
        unique_jobs: list[Job] = []
        duplicates: list[DuplicateRecord] = []

        seen_source_job_ids: dict[tuple[str, str], Job] = {}
        seen_application_urls: dict[str, Job] = {}
        seen_source_urls: dict[str, Job] = {}

        for job in jobs:
            duplicate = self._find_duplicate(
                job,
                seen_source_job_ids,
                seen_application_urls,
                seen_source_urls,
            )

            if duplicate is not None:
                kept_job, reason = duplicate

                duplicates.append(
                    DuplicateRecord(
                        duplicate_job=job,
                        kept_job=kept_job,
                        reason=reason,
                    )
                )
                continue

            unique_jobs.append(job)

            self._register_job(
                job,
                seen_source_job_ids,
                seen_application_urls,
                seen_source_urls,
            )

        return DeduplicationResult(
            unique_jobs=tuple(unique_jobs),
            duplicates=tuple(duplicates),
        )

    def _find_duplicate(
        self,
        job: Job,
        seen_source_job_ids: dict[tuple[str, str], Job],
        seen_application_urls: dict[str, Job],
        seen_source_urls: dict[str, Job],
    ) -> tuple[Job, DuplicateReason] | None:
        if job.source_job_id:
            source_job_key = (job.source, job.source_job_id)

            if source_job_key in seen_source_job_ids:
                return (
                    seen_source_job_ids[source_job_key],
                    DuplicateReason.SAME_SOURCE_JOB_ID,
                )

        application_url = str(job.application_url)

        if application_url in seen_application_urls:
            return (
                seen_application_urls[application_url],
                DuplicateReason.SAME_APPLICATION_URL,
            )

        if job.source_url:
            source_url = str(job.source_url)

            if source_url in seen_source_urls:
                return (
                    seen_source_urls[source_url],
                    DuplicateReason.SAME_SOURCE_URL,
                )

        return None

    def _register_job(
        self,
        job: Job,
        seen_source_job_ids: dict[tuple[str, str], Job],
        seen_application_urls: dict[str, Job],
        seen_source_urls: dict[str, Job],
    ) -> None:
        if job.source_job_id:
            source_job_key = (job.source, job.source_job_id)
            seen_source_job_ids[source_job_key] = job

        application_url = str(job.application_url)
        seen_application_urls[application_url] = job

        if job.source_url:
            source_url = str(job.source_url)
            seen_source_urls[source_url] = job
