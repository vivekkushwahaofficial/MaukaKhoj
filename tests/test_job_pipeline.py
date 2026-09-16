import pytest
from datetime import datetime, timezone

from app.deduplication.job import CanonicalJobDeduplicator
from app.domain.education import (
    EducationRequirement,
    EducationRequirementStatus,
)
from app.domain.job import EmploymentType, ExperienceLevel, Job, RemoteType
from app.domain.profile import Education, Profile
from app.explanation.job import DeterministicJobExplainer
from app.filtering.job import CanonicalJobHardFilter
from app.matching.job import CanonicalJobProfileMatcher
from app.normalization.base import JobNormalizer
from app.normalization.pipeline import NormalizationPipeline
from app.normalization.registry import NormalizationRegistry
from app.pipeline.job import JobPipeline
from app.ranking.job import DeterministicJobRanker
from app.scoring.job import DeterministicJobScorer
from app.sources.base import JobSourceAdapter
from app.validation.job import CanonicalJobValidator


class FakeSourceAdapter(JobSourceAdapter):
    """Test source adapter implementing the production source contract."""

    def __init__(
        self,
        source: str,
        jobs: list[dict],
        error: Exception | None = None,
    ) -> None:
        self._source = source
        self._jobs = jobs
        self._error = error

    @property
    def source_name(self) -> str:
        return self._source

    @property
    def source_id(self) -> str:
        return self._source

    def fetch_jobs(self) -> list[dict]:
        if self._error is not None:
            raise self._error

        return self._jobs


class FakeNormalizer(JobNormalizer):
    """Test normalizer that validates already-canonical job dictionaries."""

    def normalize(self, raw_job: dict) -> Job:
        return Job.model_validate(raw_job)


def make_job(
    job_id: str,
    *,
    source: str = "test",
    title: str = "Backend Engineer",
    remote_type: RemoteType = RemoteType.INDIA_REMOTE,
    posted_at: datetime | None = None,
) -> Job:
    return Job(
        job_id=job_id,
        source=source,
        source_job_id=job_id,
        company="Example Corp",
        title=title,
        description="Build backend systems using Java and Spring Boot.",
        location="India",
        remote_type=remote_type,
        employment_type=EmploymentType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY_LEVEL,
        skills=["Java", "Spring Boot"],
        application_url=f"https://example.com/jobs/{job_id}",
        posted_at=posted_at or datetime(2026, 9, 14, tzinfo=timezone.utc),
    )


def make_raw_job(job_id: str) -> dict:
    return make_job(job_id).model_dump(mode="json")


def make_profile() -> Profile:
    return Profile(
        name="Test User",
        target_titles=[
            "Backend Engineer",
            "Backend Developer",
            "Software Engineer",
        ],
        skills=["Java", "Spring Boot"],
        locations=["India"],
        remote_preferences=["INDIA_REMOTE"],
        employment_preferences=["FULL_TIME"],
        domains=["backend"],
    )


def make_pipeline(
    *,
    source_adapters: list[JobSourceAdapter],
) -> JobPipeline:
    registry = NormalizationRegistry()
    registry.register("test", FakeNormalizer())

    return JobPipeline(
        source_adapters=source_adapters,
        normalization_pipeline=NormalizationPipeline(registry),
        validator=CanonicalJobValidator(),
        deduplicator=CanonicalJobDeduplicator(),
        hard_filter=CanonicalJobHardFilter(),
        matcher=CanonicalJobProfileMatcher(),
        scorer=DeterministicJobScorer(),
        ranker=DeterministicJobRanker(),
        explainer=DeterministicJobExplainer(),
    )


def test_pipeline_processes_jobs_through_all_stages() -> None:
    adapter = FakeSourceAdapter(
        "test",
        [make_raw_job("job-1")],
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile(), limit=5)

    assert len(result.processed_jobs) == 1

    processed = result.processed_jobs[0]

    assert processed.job.job_id == "job-1"
    assert processed.match_result.role.matched is True
    assert processed.job_score.total > 0
    assert processed.explanation.summary
    assert processed.rank == 1


def test_pipeline_combines_jobs_from_multiple_sources() -> None:
    first = FakeSourceAdapter(
        "test",
        [make_raw_job("job-1")],
    )
    second = FakeSourceAdapter(
        "test",
        [make_raw_job("job-2")],
    )

    result = make_pipeline(
        source_adapters=[first, second],
    ).run(make_profile())

    assert [item.job.job_id for item in result.processed_jobs] == [
        "job-1",
        "job-2",
    ]


def test_pipeline_records_validation_results() -> None:
    adapter = FakeSourceAdapter(
        "test",
        [make_raw_job("job-1")],
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile())

    assert len(result.validation_results) == 1
    assert result.validation_results[0].is_valid is True


def test_pipeline_excludes_invalid_jobs() -> None:
    invalid_job = make_job("job-1").model_construct(
        application_url="not-a-valid-url",
    )

    class InvalidJobNormalizer(JobNormalizer):
        def normalize(self, raw_job: dict) -> Job:
            return invalid_job

    registry = NormalizationRegistry()
    registry.register("test", InvalidJobNormalizer())

    pipeline = JobPipeline(
        source_adapters=[
            FakeSourceAdapter(
                "test",
                [make_raw_job("job-1")],
            )
        ],
        normalization_pipeline=NormalizationPipeline(registry),
        validator=CanonicalJobValidator(),
        deduplicator=CanonicalJobDeduplicator(),
        hard_filter=CanonicalJobHardFilter(),
        matcher=CanonicalJobProfileMatcher(),
        scorer=DeterministicJobScorer(),
        ranker=DeterministicJobRanker(),
        explainer=DeterministicJobExplainer(),
    )

    result = pipeline.run(make_profile())

    assert result.processed_jobs == ()
    assert len(result.validation_results) == 1
    assert result.validation_results[0].is_valid is False


def test_pipeline_deduplicates_jobs_before_matching() -> None:
    first = FakeSourceAdapter(
        "test",
        [make_raw_job("job-1")],
    )
    second = FakeSourceAdapter(
        "test",
        [make_raw_job("job-1")],
    )

    result = make_pipeline(
        source_adapters=[first, second],
    ).run(make_profile())

    assert len(result.processed_jobs) == 1
    assert len(result.duplicates) == 1
    assert result.duplicates[0].duplicate_job.job_id == "job-1"


def test_pipeline_records_hard_filter_rejections() -> None:
    onsite_job = make_raw_job("job-1")
    onsite_job["remote_type"] = RemoteType.ONSITE.value

    adapter = FakeSourceAdapter(
        "test",
        [onsite_job],
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile())

    assert result.processed_jobs == ()
    assert len(result.rejected_jobs) == 1
    assert result.rejected_jobs[0].job.job_id == "job-1"
    assert result.rejected_jobs[0].reason.value == "ONSITE"


def test_pipeline_ranks_processed_jobs() -> None:
    first = make_raw_job("job-1")
    second = make_raw_job("job-2")

    first["posted_at"] = "2026-09-10T00:00:00Z"
    second["posted_at"] = "2026-09-14T00:00:00Z"

    adapter = FakeSourceAdapter(
        "test",
        [first, second],
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile())

    assert [item.job.job_id for item in result.processed_jobs] == [
        "job-2",
        "job-1",
    ]
    assert [item.rank for item in result.processed_jobs] == [1, 2]


def test_pipeline_applies_selection_limit() -> None:
    jobs = [
        make_raw_job("job-1"),
        make_raw_job("job-2"),
        make_raw_job("job-3"),
    ]

    adapter = FakeSourceAdapter("test", jobs)

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile(), limit=2)

    assert len(result.processed_jobs) == 2
    assert [item.rank for item in result.processed_jobs] == [1, 2]


def test_pipeline_continues_when_one_source_fails() -> None:
    failing = FakeSourceAdapter(
        "failing",
        [],
        error=RuntimeError("Source unavailable."),
    )
    working = FakeSourceAdapter(
        "test",
        [make_raw_job("job-1")],
    )

    result = make_pipeline(
        source_adapters=[failing, working],
    ).run(make_profile())

    assert len(result.processed_jobs) == 1
    assert len(result.source_failures) == 1
    assert result.source_failures[0].source == "failing"
    assert result.source_failures[0].error == "Source unavailable."


def test_pipeline_returns_empty_result_when_no_jobs_are_available() -> None:
    adapter = FakeSourceAdapter("test", [])

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile())

    assert result.processed_jobs == ()
    assert result.validation_results == ()
    assert result.duplicates == ()
    assert result.rejected_jobs == ()
    assert result.source_failures == ()


def test_pipeline_rejects_negative_limit() -> None:
    adapter = FakeSourceAdapter(
        "test",
        [make_raw_job("job-1")],
    )

    try:
        make_pipeline(
            source_adapters=[adapter],
        ).run(make_profile(), limit=-1)
    except ValueError as exc:
        assert "negative" in str(exc).lower()
    else:
        raise AssertionError("Pipeline should reject a negative limit.")


def test_pipeline_excludes_jobs_without_core_profile_relevance() -> None:
    relevant = make_job(
        "job-relevant",
        title="Backend Engineer",
    ).model_dump(mode="json")

    irrelevant = make_job(
        "job-irrelevant",
        title="Marketing Manager",
    ).model_dump(mode="json")

    irrelevant["description"] = "Create marketing campaigns."
    irrelevant["skills"] = ["Marketing", "SEO"]

    adapter = FakeSourceAdapter(
        "test",
        [relevant, irrelevant],
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile())

    assert [item.job.job_id for item in result.processed_jobs] == [
        "job-relevant",
    ]


# ---------------------------------------------------------------------------
# Seniority and management filtering
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "title",
    [
        "Staff Software Engineer",
        "Senior Software Engineer",
        "Sr. Software Engineer",
        "Principal Software Engineer",
        "Distinguished Engineer",
        "Fellow Engineer",
        "Lead Software Engineer",
        "Tech Lead",
        "Team Lead",
        "Software Architect",
        "Engineering Manager",
        "Software Engineering Director",
        "VP Engineering",
        "Vice President Engineering",
        "Head of Engineering",
        "Chief Technology Officer",
        "CTO",
    ],
)
def test_senior_or_management_titles_are_excluded(title: str) -> None:
    assert JobPipeline._is_senior_or_management_title(title) is True


@pytest.mark.parametrize(
    "title",
    [
        "Software Engineer",
        "Junior Software Engineer",
        "Software Engineer Intern",
        "Backend Engineer",
        "Backend Developer",
        "Java Developer",
        "Full Stack Developer",
        "Graduate Software Engineer",
        "Trainee Software Engineer",
        "Associate Software Engineer",
    ],
)
def test_entry_level_titles_are_not_excluded(title: str) -> None:
    assert JobPipeline._is_senior_or_management_title(title) is False


def test_pipeline_excludes_staff_software_engineer() -> None:
    staff_job = make_raw_job("staff-job")
    staff_job["title"] = "Staff Software Engineer"

    adapter = FakeSourceAdapter(
        "test",
        [staff_job],
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile())

    assert result.profile_matched_jobs == ()
    assert result.processed_jobs == ()


def test_pipeline_keeps_regular_software_engineer() -> None:
    regular_job = make_raw_job("regular-job")
    regular_job["title"] = "Software Engineer"
    regular_job["description"] = (
        "Build software systems using Java, Spring Boot, " "and backend technologies."
    )

    adapter = FakeSourceAdapter(
        "test",
        [regular_job],
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile())

    assert len(result.profile_matched_jobs) == 1
    assert result.profile_matched_jobs[0].job.job_id == "regular-job"


# ---------------------------------------------------------------------------
# Education filtering
# ---------------------------------------------------------------------------


def test_pipeline_excludes_explicit_education_requirement_without_profile() -> None:
    job = make_job("education-required")
    job.education_requirement = EducationRequirement(
        status=EducationRequirementStatus.REQUIRED,
        degree="B.Tech",
        field="Computer Science",
    )

    adapter = FakeSourceAdapter(
        "test",
        [job.model_dump(mode="json")],
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(make_profile())

    assert result.profile_matched_jobs == ()
    assert result.processed_jobs == ()


def test_pipeline_keeps_job_without_education_requirement() -> None:
    """
    A job with no explicit education requirement remains eligible
    when the profile has no education information.
    """

    job = make_job(
        "education-unknown",
    )

    adapter = FakeSourceAdapter(
        "test",
        [job.model_dump(mode="json")],
    )

    # Keep the normal profile relevance settings while leaving education
    # unconfigured. This isolates the education behavior under test.
    profile = make_profile().model_copy(
        update={
            "education": Education(),
        }
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(profile)

    assert len(result.profile_matched_jobs) == 1
    assert result.profile_matched_jobs[0].match_result.education.matched is None


def test_pipeline_accepts_matching_btech_profile() -> None:
    job = make_job("education-btech")
    job.education_requirement = EducationRequirement(
        status=EducationRequirementStatus.REQUIRED,
        degree="B.Tech",
        field="Computer Science",
    )

    adapter = FakeSourceAdapter(
        "test",
        [job.model_dump(mode="json")],
    )

    profile = make_profile().model_copy(
        update={
            "education": Education(
                degree="B.Tech",
                field="Computer Science",
                graduation_year=2027,
                is_running=True,
            ),
        }
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(profile)

    assert len(result.profile_matched_jobs) == 1
    assert result.profile_matched_jobs[0].match_result.education.matched is True


def test_pipeline_excludes_wrong_degree() -> None:
    job = make_job("education-wrong-degree")
    job.education_requirement = EducationRequirement(
        status=EducationRequirementStatus.REQUIRED,
        degree="Master's degree",
        field="Computer Science",
    )

    adapter = FakeSourceAdapter(
        "test",
        [job.model_dump(mode="json")],
    )

    profile = make_profile().model_copy(
        update={
            "education": Education(
                degree="B.Tech",
                field="Computer Science",
                graduation_year=2027,
                is_running=True,
            ),
        }
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(profile)

    assert result.profile_matched_jobs == ()
    assert result.processed_jobs == ()


def test_pipeline_accepts_current_student_when_job_allows_students() -> None:
    job = make_job("education-current-student")
    job.education_requirement = EducationRequirement(
        status=EducationRequirementStatus.REQUIRED,
        degree="B.Tech",
        field="Computer Science",
        accepts_current_students=True,
    )

    adapter = FakeSourceAdapter(
        "test",
        [job.model_dump(mode="json")],
    )

    profile = make_profile().model_copy(
        update={
            "education": Education(
                degree="B.Tech",
                field="Computer Science",
                graduation_year=2027,
                is_running=True,
            ),
        }
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(profile)

    assert len(result.profile_matched_jobs) == 1
    assert result.profile_matched_jobs[0].match_result.education.matched is True


def test_pipeline_excludes_current_student_when_job_does_not_allow_students() -> None:
    job = make_job("education-student-not-allowed")
    job.education_requirement = EducationRequirement(
        status=EducationRequirementStatus.REQUIRED,
        degree="B.Tech",
        field="Computer Science",
        accepts_current_students=False,
    )

    adapter = FakeSourceAdapter(
        "test",
        [job.model_dump(mode="json")],
    )

    profile = make_profile().model_copy(
        update={
            "education": Education(
                degree="B.Tech",
                field="Computer Science",
                graduation_year=2027,
                is_running=True,
            ),
        }
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(profile)

    assert result.profile_matched_jobs == ()
    assert result.processed_jobs == ()


def test_pipeline_excludes_late_graduation_year() -> None:
    job = make_job("education-graduation-year")
    job.education_requirement = EducationRequirement(
        status=EducationRequirementStatus.REQUIRED,
        degree="B.Tech",
        field="Computer Science",
        minimum_graduation_year=2024,
        maximum_graduation_year=2026,
    )

    adapter = FakeSourceAdapter(
        "test",
        [job.model_dump(mode="json")],
    )

    profile = make_profile().model_copy(
        update={
            "education": Education(
                degree="B.Tech",
                field="Computer Science",
                graduation_year=2027,
                is_running=True,
            ),
        }
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(profile)

    assert result.profile_matched_jobs == ()
    assert result.processed_jobs == ()


def test_pipeline_accepts_matching_graduation_range() -> None:
    job = make_job("education-graduation-range")
    job.education_requirement = EducationRequirement(
        status=EducationRequirementStatus.REQUIRED,
        degree="B.Tech",
        field="Computer Science",
        minimum_graduation_year=2026,
        maximum_graduation_year=2028,
    )

    adapter = FakeSourceAdapter(
        "test",
        [job.model_dump(mode="json")],
    )

    profile = make_profile().model_copy(
        update={
            "education": Education(
                degree="B.Tech",
                field="Computer Science",
                graduation_year=2027,
                is_running=True,
            ),
        }
    )

    result = make_pipeline(
        source_adapters=[adapter],
    ).run(profile)

    assert len(result.profile_matched_jobs) == 1
    assert result.profile_matched_jobs[0].match_result.education.matched is True
