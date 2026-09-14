from datetime import datetime

import pytest

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.filtering.job import CanonicalJobHardFilter
from app.filtering.models import RejectionReason


def create_job(
    *,
    job_id: str,
    remote_type: RemoteType,
) -> Job:
    return Job(
        job_id=job_id,
        source="lever",
        source_job_id=f"lever-{job_id}",
        company="Example Company",
        title="Software Engineer",
        description="Backend engineering role.",
        location="India",
        remote_type=remote_type,
        employment_type=EmploymentType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY_LEVEL,
        skills=["Python"],
        posted_at=datetime(2026, 9, 14),
        application_url=f"https://example.com/apply/{job_id}",
        source_url=f"https://example.com/jobs/{job_id}",
    )


@pytest.mark.parametrize(
    "remote_type",
    [
        RemoteType.INDIA_REMOTE,
        RemoteType.COUNTRY_REMOTE,
        RemoteType.REGION_REMOTE,
        RemoteType.WORLDWIDE_REMOTE,
        RemoteType.UNKNOWN,
    ],
)
def test_all_non_rejected_remote_types_are_eligible(
    remote_type: RemoteType,
) -> None:
    job = create_job(
        job_id="1",
        remote_type=remote_type,
    )

    result = CanonicalJobHardFilter().filter([job])

    assert result.eligible_jobs == (job,)
    assert result.rejected_jobs == ()


def test_onsite_job_is_rejected() -> None:
    job = create_job(
        job_id="1",
        remote_type=RemoteType.ONSITE,
    )

    result = CanonicalJobHardFilter().filter([job])

    assert result.eligible_jobs == ()
    assert len(result.rejected_jobs) == 1
    assert result.rejected_jobs[0].job == job
    assert result.rejected_jobs[0].reason == RejectionReason.ONSITE


def test_hybrid_job_is_rejected() -> None:
    job = create_job(
        job_id="1",
        remote_type=RemoteType.HYBRID,
    )

    result = CanonicalJobHardFilter().filter([job])

    assert result.eligible_jobs == ()
    assert len(result.rejected_jobs) == 1
    assert result.rejected_jobs[0].job == job
    assert result.rejected_jobs[0].reason == RejectionReason.HYBRID


def test_mixed_jobs_are_partitioned_correctly() -> None:
    remote_job = create_job(
        job_id="1",
        remote_type=RemoteType.INDIA_REMOTE,
    )
    onsite_job = create_job(
        job_id="2",
        remote_type=RemoteType.ONSITE,
    )
    hybrid_job = create_job(
        job_id="3",
        remote_type=RemoteType.HYBRID,
    )
    unknown_job = create_job(
        job_id="4",
        remote_type=RemoteType.UNKNOWN,
    )

    result = CanonicalJobHardFilter().filter(
        [
            remote_job,
            onsite_job,
            hybrid_job,
            unknown_job,
        ]
    )

    assert result.eligible_jobs == (
        remote_job,
        unknown_job,
    )

    assert len(result.rejected_jobs) == 2
    assert result.rejected_jobs[0].job == onsite_job
    assert result.rejected_jobs[0].reason == RejectionReason.ONSITE
    assert result.rejected_jobs[1].job == hybrid_job
    assert result.rejected_jobs[1].reason == RejectionReason.HYBRID


def test_empty_job_list_returns_empty_result() -> None:
    result = CanonicalJobHardFilter().filter([])

    assert result.eligible_jobs == ()
    assert result.rejected_jobs == ()
