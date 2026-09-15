from app.domain.job import EmploymentType, ExperienceLevel, Job, RemoteType
from datetime import datetime, timedelta, timezone

import pytest

from app.domain.job import EmploymentType, ExperienceLevel, Job, RemoteType
from app.domain.profile import Experience, Profile
from app.matching.models import MatchDimension, MatchResult
from app.scoring.job import DeterministicJobScorer


@pytest.fixture
def scorer() -> DeterministicJobScorer:
    return DeterministicJobScorer()


@pytest.fixture
def profile() -> Profile:
    return Profile(
        name="Candidate",
        target_titles=["Java Developer"],
        skills=["Java", "Spring Boot", "PostgreSQL"],
        experience=Experience(
            years=1.0,
            current_title="Java Developer",
        ),
        locations=["India"],
        remote_preferences=["INDIA_REMOTE"],
        employment_preferences=["FULL_TIME"],
    )


def create_job(
    *,
    posted_at: datetime | None = None,
    experience_level: ExperienceLevel = ExperienceLevel.ENTRY_LEVEL,
    employment_type: EmploymentType = EmploymentType.FULL_TIME,
    remote_type: RemoteType = RemoteType.INDIA_REMOTE,
) -> Job:
    return Job(
        job_id="job-1",
        source="test",
        source_job_id="source-1",
        company="Example Corp",
        title="Java Developer",
        description="Java backend development role.",
        location="India",
        remote_type=remote_type,
        employment_type=employment_type,
        experience_level=experience_level,
        skills=["Java", "Spring Boot", "PostgreSQL"],
        posted_at=posted_at,
        application_url="https://example.com/jobs/job-1",
        company_url="https://example.com",
        source_url="https://example.com/jobs/job-1",
    )


def create_match_result(
    *,
    role: bool | None = True,
    skills: bool | None = True,
    experience: bool | None = True,
    location: bool | None = True,
    employment: bool | None = True,
    skill_matches: tuple[str, ...] = (
        "Java",
        "Spring Boot",
        "PostgreSQL",
    ),
    missing_skills: tuple[str, ...] = (),
) -> MatchResult:
    return MatchResult(
        role=MatchDimension(
            matched=role,
            evidence=("Role evidence.",),
        ),
        skills=MatchDimension(
            matched=skills,
            matched_values=skill_matches,
            missing_values=missing_skills,
            evidence=("Skills evidence.",),
        ),
        experience=MatchDimension(
            matched=experience,
            evidence=("Experience evidence.",),
        ),
        education=MatchDimension(
            matched=None,
            evidence=("Education is unknown.",),
        ),
        location=MatchDimension(
            matched=location,
            evidence=("Location evidence.",),
        ),
        remote=MatchDimension(
            matched=None,
            evidence=("Remote evidence.",),
        ),
        employment=MatchDimension(
            matched=employment,
            evidence=("Employment evidence.",),
        ),
        domain=MatchDimension(
            matched=None,
            evidence=("Domain is unknown.",),
        ),
    )


def test_fully_matched_job_scores_100(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)
    job = create_job(posted_at=now)

    result = scorer.score(
        job,
        profile,
        create_match_result(),
        now=now,
    )

    assert result.total == 100.0
    assert result.role.score == 25.0
    assert result.skills.score == 30.0
    assert result.experience.score == 20.0
    assert result.location.score == 15.0
    assert result.freshness.score == 5.0
    assert result.employment.score == 5.0


def test_skills_are_scored_proportionally(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    result = scorer.score(
        create_job(),
        profile,
        create_match_result(
            skill_matches=("Java", "Spring Boot"),
            missing_skills=("PostgreSQL",),
        ),
    )

    assert result.skills.score == 20.0
    assert result.skills.max_score == 30.0


def test_role_mismatch_contributes_zero(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    result = scorer.score(
        create_job(),
        profile,
        create_match_result(role=False),
    )

    assert result.role.score == 0.0
    assert result.role.max_score == 25.0


def test_experience_mismatch_contributes_zero(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    result = scorer.score(
        create_job(),
        profile,
        create_match_result(experience=False),
    )

    assert result.experience.score == 0.0
    assert result.experience.max_score == 20.0


def test_location_mismatch_contributes_zero(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    result = scorer.score(
        create_job(),
        profile,
        create_match_result(location=False),
    )

    assert result.location.score == 0.0
    assert result.location.max_score == 15.0


def test_employment_mismatch_contributes_zero(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    result = scorer.score(
        create_job(),
        profile,
        create_match_result(employment=False),
    )

    assert result.employment.score == 0.0
    assert result.employment.max_score == 5.0


@pytest.mark.parametrize(
    ("age_days", "expected_score"),
    [
        (0, 5.0),
        (1, 5.0),
        (2, 4.0),
        (3, 4.0),
        (7, 3.0),
        (14, 2.0),
        (30, 1.0),
        (31, 0.0),
    ],
)
def test_freshness_score_uses_expected_age_buckets(
    scorer: DeterministicJobScorer,
    profile: Profile,
    age_days: int,
    expected_score: float,
) -> None:
    now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)
    posted_at = now - timedelta(days=age_days)

    result = scorer.score(
        create_job(posted_at=posted_at),
        profile,
        create_match_result(),
        now=now,
    )

    assert result.freshness.score == expected_score


def test_unknown_dimensions_are_excluded_from_final_score(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)

    result = scorer.score(
        create_job(posted_at=now),
        profile,
        create_match_result(
            role=True,
            skills=True,
            experience=True,
            location=None,
            employment=None,
        ),
        now=now,
    )

    assert result.total == 100.0
    assert result.location.score == 0.0
    assert result.employment.score == 0.0


def test_unknown_posting_date_is_excluded_from_final_score(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    result = scorer.score(
        create_job(posted_at=None),
        profile,
        create_match_result(),
    )

    assert result.total == 100.0
    assert result.freshness.score == 0.0
    assert result.freshness.max_score == 5.0


def test_score_is_deterministic_with_fixed_reference_time(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)
    job = create_job(
        posted_at=now - timedelta(days=3),
    )
    match_result = create_match_result()

    first = scorer.score(
        job,
        profile,
        match_result,
        now=now,
    )
    second = scorer.score(
        job,
        profile,
        match_result,
        now=now,
    )

    assert first == second


def test_naive_and_aware_datetimes_are_handled_consistently(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    naive_now = datetime(2026, 9, 14, 12)
    aware_now = naive_now.replace(tzinfo=timezone.utc)

    naive_job = create_job(
        posted_at=naive_now - timedelta(days=2),
    )
    aware_job = create_job(
        posted_at=aware_now - timedelta(days=2),
    )

    match_result = create_match_result()

    naive_result = scorer.score(
        naive_job,
        profile,
        match_result,
        now=naive_now,
    )
    aware_result = scorer.score(
        aware_job,
        profile,
        match_result,
        now=aware_now,
    )

    assert naive_result.freshness.score == aware_result.freshness.score
    assert naive_result.total == aware_result.total


def test_explanation_contains_overall_score(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)

    result = scorer.score(
        create_job(posted_at=now),
        profile,
        create_match_result(),
        now=now,
    )

    assert result.explanation[0] == ("Overall deterministic match score: 100.00/100.")


def test_score_is_normalized_when_some_dimensions_are_unknown(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)

    result = scorer.score(
        create_job(posted_at=now),
        profile,
        create_match_result(
            role=True,
            skills=True,
            experience=False,
            location=None,
            employment=True,
        ),
        now=now,
    )

    # Known weights:
    # role=25 + skills=30 + experience=20 + freshness=5 + employment=5
    # = 85.
    # Earned: 25 + 30 + 0 + 5 + 5 = 65.
    # 65 / 85 * 100 = 76.47.
    assert result.total == 76.47


def test_all_unknown_weighted_dimensions_return_zero(
    scorer: DeterministicJobScorer,
    profile: Profile,
) -> None:
    result = scorer.score(
        create_job(posted_at=None),
        profile,
        create_match_result(
            role=None,
            skills=None,
            experience=None,
            location=None,
            employment=None,
        ),
    )

    assert result.total == 0.0
