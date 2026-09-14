from datetime import datetime, timezone

import pytest

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.ranking.job import DeterministicJobRanker
from app.scoring.models import JobScore, ScoreDimension


def make_job(
    job_id: str,
    company: str = "Company",
    title: str = "Software Engineer",
    posted_at: datetime | None = None,
) -> Job:
    return Job(
        job_id=job_id,
        source="test",
        source_job_id=job_id,
        company=company,
        title=title,
        description="Test job description",
        location="India",
        remote_type=RemoteType.INDIA_REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY_LEVEL,
        application_url=f"https://example.com/jobs/{job_id}",
        posted_at=posted_at,
    )


def make_score(total: float) -> JobScore:
    dimension = ScoreDimension(
        score=total,
        max_score=total,
        evidence=("test",),
    )

    return JobScore(
        total=total,
        role=dimension,
        skills=dimension,
        experience=dimension,
        location=dimension,
        freshness=dimension,
        employment=dimension,
    )


def test_rank_orders_jobs_by_score_descending() -> None:
    jobs = [
        (make_job("job-1"), make_score(70)),
        (make_job("job-2"), make_score(95)),
        (make_job("job-3"), make_score(80)),
    ]

    result = DeterministicJobRanker().rank(jobs)

    assert [item.job.job_id for item in result.ranked_jobs] == [
        "job-2",
        "job-3",
        "job-1",
    ]


def test_rank_uses_newest_posted_at_as_first_tiebreaker() -> None:
    jobs = [
        (
            make_job(
                "older",
                posted_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
            ),
            make_score(90),
        ),
        (
            make_job(
                "newer",
                posted_at=datetime(2026, 9, 14, tzinfo=timezone.utc),
            ),
            make_score(90),
        ),
    ]

    result = DeterministicJobRanker().rank(jobs)

    assert [item.job.job_id for item in result.ranked_jobs] == [
        "newer",
        "older",
    ]


def test_rank_uses_company_as_second_tiebreaker() -> None:
    jobs = [
        (make_job("job-a", company="Zeta"), make_score(90)),
        (make_job("job-b", company="Alpha"), make_score(90)),
    ]

    result = DeterministicJobRanker().rank(jobs)

    assert [item.job.job_id for item in result.ranked_jobs] == [
        "job-b",
        "job-a",
    ]


def test_rank_uses_title_as_third_tiebreaker() -> None:
    jobs = [
        (
            make_job("job-a", company="Same", title="Zebra Engineer"),
            make_score(90),
        ),
        (
            make_job("job-b", company="Same", title="Backend Engineer"),
            make_score(90),
        ),
    ]

    result = DeterministicJobRanker().rank(jobs)

    assert [item.job.job_id for item in result.ranked_jobs] == [
        "job-b",
        "job-a",
    ]


def test_rank_uses_job_id_as_final_tiebreaker() -> None:
    jobs = [
        (
            make_job("job-z", company="Same", title="Same"),
            make_score(90),
        ),
        (
            make_job("job-a", company="Same", title="Same"),
            make_score(90),
        ),
    ]

    result = DeterministicJobRanker().rank(jobs)

    assert [item.job.job_id for item in result.ranked_jobs] == [
        "job-a",
        "job-z",
    ]


def test_rank_assigns_sequential_ranks() -> None:
    jobs = [
        (make_job("job-1"), make_score(70)),
        (make_job("job-2"), make_score(90)),
        (make_job("job-3"), make_score(80)),
    ]

    result = DeterministicJobRanker().rank(jobs)

    assert [item.rank for item in result.ranked_jobs] == [1, 2, 3]


def test_rank_selects_top_jobs_when_limit_is_provided() -> None:
    jobs = [
        (make_job("job-1"), make_score(70)),
        (make_job("job-2"), make_score(95)),
        (make_job("job-3"), make_score(80)),
    ]

    result = DeterministicJobRanker().rank(jobs, limit=2)

    assert [item.job.job_id for item in result.selected_jobs] == [
        "job-2",
        "job-3",
    ]

    assert len(result.ranked_jobs) == 3
    assert len(result.selected_jobs) == 2


def test_rank_with_zero_limit_selects_no_jobs() -> None:
    jobs = [
        (make_job("job-1"), make_score(90)),
        (make_job("job-2"), make_score(80)),
    ]

    result = DeterministicJobRanker().rank(jobs, limit=0)

    assert result.ranked_jobs
    assert result.selected_jobs == ()


def test_rank_rejects_negative_limit() -> None:
    jobs = [(make_job("job-1"), make_score(90))]

    with pytest.raises(ValueError, match="cannot be negative"):
        DeterministicJobRanker().rank(jobs, limit=-1)


def test_rank_places_unknown_posted_at_after_known_date() -> None:
    jobs = [
        (make_job("unknown"), make_score(90)),
        (
            make_job(
                "known",
                posted_at=datetime(2026, 9, 14, tzinfo=timezone.utc),
            ),
            make_score(90),
        ),
    ]

    result = DeterministicJobRanker().rank(jobs)

    assert [item.job.job_id for item in result.ranked_jobs] == [
        "known",
        "unknown",
    ]


def test_rank_handles_naive_and_aware_posted_at_consistently() -> None:
    jobs = [
        (
            make_job(
                "naive",
                posted_at=datetime(2026, 9, 14, 10, 0),
            ),
            make_score(90),
        ),
        (
            make_job(
                "aware",
                posted_at=datetime(
                    2026,
                    9,
                    14,
                    11,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            make_score(90),
        ),
    ]

    result = DeterministicJobRanker().rank(jobs)

    assert [item.job.job_id for item in result.ranked_jobs] == [
        "aware",
        "naive",
    ]


def test_rank_returns_empty_result_for_empty_input() -> None:
    result = DeterministicJobRanker().rank([])

    assert result.ranked_jobs == ()
    assert result.selected_jobs == ()
