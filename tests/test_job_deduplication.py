from datetime import datetime

from app.deduplication.job import CanonicalJobDeduplicator
from app.deduplication.models import DuplicateReason
from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)


def create_job(
    *,
    job_id: str,
    source: str = "lever",
    source_job_id: str | None = None,
    application_url: str = "https://example.com/apply/1",
    source_url: str | None = "https://example.com/jobs/1",
) -> Job:
    return Job(
        job_id=job_id,
        source=source,
        source_job_id=source_job_id,
        company="Example Company",
        title="Software Engineer",
        description="Backend engineering role.",
        location="India",
        remote_type=RemoteType.INDIA_REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY_LEVEL,
        skills=["Python"],
        posted_at=datetime(2026, 9, 14),
        application_url=application_url,
        source_url=source_url,
    )


def test_keeps_unique_jobs() -> None:
    jobs = [
        create_job(
            job_id="1",
            source_job_id="lever-1",
            application_url="https://example.com/apply/1",
            source_url="https://example.com/jobs/1",
        ),
        create_job(
            job_id="2",
            source_job_id="lever-2",
            application_url="https://example.com/apply/2",
            source_url="https://example.com/jobs/2",
        ),
    ]

    result = CanonicalJobDeduplicator().deduplicate(jobs)

    assert len(result.unique_jobs) == 2
    assert len(result.duplicates) == 0


def test_deduplicates_same_source_and_source_job_id() -> None:
    first = create_job(
        job_id="1",
        source="lever",
        source_job_id="lever-123",
        application_url="https://example.com/apply/1",
        source_url="https://example.com/jobs/1",
    )

    duplicate = create_job(
        job_id="2",
        source="lever",
        source_job_id="lever-123",
        application_url="https://example.com/apply/2",
        source_url="https://example.com/jobs/2",
    )

    result = CanonicalJobDeduplicator().deduplicate([first, duplicate])

    assert len(result.unique_jobs) == 1
    assert len(result.duplicates) == 1
    assert result.duplicates[0].kept_job == first
    assert result.duplicates[0].duplicate_job == duplicate
    assert result.duplicates[0].reason == DuplicateReason.SAME_SOURCE_JOB_ID


def test_same_source_job_id_from_different_sources_is_not_duplicate() -> None:
    first = create_job(
        job_id="1",
        source="lever",
        source_job_id="123",
        application_url="https://example.com/apply/1",
        source_url="https://example.com/jobs/1",
    )

    second = create_job(
        job_id="2",
        source="ashby",
        source_job_id="123",
        application_url="https://example.com/apply/2",
        source_url="https://example.com/jobs/2",
    )

    result = CanonicalJobDeduplicator().deduplicate([first, second])

    assert len(result.unique_jobs) == 2
    assert len(result.duplicates) == 0


def test_deduplicates_same_application_url() -> None:
    first = create_job(
        job_id="1",
        source_job_id="lever-1",
        application_url="https://example.com/apply/shared",
        source_url="https://example.com/jobs/1",
    )

    duplicate = create_job(
        job_id="2",
        source_job_id="lever-2",
        application_url="https://example.com/apply/shared",
        source_url="https://example.com/jobs/2",
    )

    result = CanonicalJobDeduplicator().deduplicate([first, duplicate])

    assert len(result.unique_jobs) == 1
    assert result.duplicates[0].reason == DuplicateReason.SAME_APPLICATION_URL


def test_deduplicates_same_source_url() -> None:
    first = create_job(
        job_id="1",
        source_job_id="lever-1",
        application_url="https://example.com/apply/1",
        source_url="https://example.com/jobs/shared",
    )

    duplicate = create_job(
        job_id="2",
        source_job_id="lever-2",
        application_url="https://example.com/apply/2",
        source_url="https://example.com/jobs/shared",
    )

    result = CanonicalJobDeduplicator().deduplicate([first, duplicate])

    assert len(result.unique_jobs) == 1
    assert result.duplicates[0].reason == DuplicateReason.SAME_SOURCE_URL


def test_missing_source_job_id_does_not_break_deduplication() -> None:
    first = create_job(
        job_id="1",
        source_job_id=None,
        application_url="https://example.com/apply/1",
        source_url="https://example.com/jobs/1",
    )

    second = create_job(
        job_id="2",
        source_job_id=None,
        application_url="https://example.com/apply/2",
        source_url="https://example.com/jobs/2",
    )

    result = CanonicalJobDeduplicator().deduplicate([first, second])

    assert len(result.unique_jobs) == 2
    assert len(result.duplicates) == 0


def test_source_job_id_duplicate_has_priority_over_url_duplicate() -> None:
    first = create_job(
        job_id="1",
        source_job_id="same-id",
        application_url="https://example.com/apply/shared",
    )

    second = create_job(
        job_id="2",
        source_job_id="same-id",
        application_url="https://example.com/apply/shared",
    )

    result = CanonicalJobDeduplicator().deduplicate([first, second])

    assert result.duplicates[0].reason == DuplicateReason.SAME_SOURCE_JOB_ID
