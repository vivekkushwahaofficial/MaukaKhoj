from datetime import datetime, timedelta, timezone

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
    posted_at: datetime | None = None,
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
        posted_at=posted_at,
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


def test_hard_filter_rejects_stale_jobs() -> None:
    stale_job = create_job(
        job_id="job-stale",
        remote_type=RemoteType.INDIA_REMOTE,
        posted_at=datetime.now(timezone.utc) - timedelta(days=31),
    )

    result = CanonicalJobHardFilter(
        freshness_config={
            "enabled": True,
            "max_age_days": 30,
        },
    ).filter([stale_job])

    assert result.eligible_jobs == ()
    assert len(result.rejected_jobs) == 1
    assert result.rejected_jobs[0].job.job_id == "job-stale"
    assert result.rejected_jobs[0].reason == RejectionReason.STALE


def test_hard_filter_keeps_fresh_jobs() -> None:
    fresh_job = create_job(
        job_id="job-fresh",
        remote_type=RemoteType.INDIA_REMOTE,
        posted_at=datetime.now(timezone.utc) - timedelta(days=29),
    )

    result = CanonicalJobHardFilter(
        freshness_config={
            "enabled": True,
            "max_age_days": 30,
        },
    ).filter([fresh_job])

    assert result.eligible_jobs == (fresh_job,)
    assert result.rejected_jobs == ()


def test_hard_filter_keeps_jobs_without_posted_at() -> None:
    undated_job = create_job(
        job_id="job-undated",
        remote_type=RemoteType.INDIA_REMOTE,
        posted_at=None,
    )

    result = CanonicalJobHardFilter(
        freshness_config={
            "enabled": True,
            "max_age_days": 30,
        },
    ).filter([undated_job])

    assert result.eligible_jobs == (undated_job,)
    assert result.rejected_jobs == ()


def test_hard_filter_keeps_future_posted_jobs() -> None:
    future_job = create_job(
        job_id="job-future",
        remote_type=RemoteType.INDIA_REMOTE,
        posted_at=datetime.now(timezone.utc) + timedelta(days=1),
    )

    result = CanonicalJobHardFilter(
        freshness_config={
            "enabled": True,
            "max_age_days": 30,
        },
    ).filter([future_job])

    assert result.eligible_jobs == (future_job,)
    assert result.rejected_jobs == ()


def test_hard_filter_can_disable_freshness() -> None:
    stale_job = create_job(
        job_id="job-stale",
        remote_type=RemoteType.INDIA_REMOTE,
        posted_at=datetime.now(timezone.utc) - timedelta(days=31),
    )

    result = CanonicalJobHardFilter(
        freshness_config={
            "enabled": False,
            "max_age_days": 30,
        },
    ).filter([stale_job])

    assert result.eligible_jobs == (stale_job,)
    assert result.rejected_jobs == ()
