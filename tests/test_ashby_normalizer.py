from datetime import datetime, timezone

import pytest

from app.domain.job import EmploymentType, ExperienceLevel, RemoteType
from app.normalization.ashby import AshbyJobNormalizer
from app.normalization.skills import SkillExtractor


def make_job(**overrides: object) -> dict:
    job = {
        "title": "Software Engineer",
        "location": "Bangalore, India",
        "isRemote": True,
        "workplaceType": "Remote",
        "descriptionPlain": (
            "Build backend systems using Java, Spring Boot, "
            "PostgreSQL, and REST APIs."
        ),
        "publishedAt": "2026-09-10T10:30:00.000+00:00",
        "employmentType": "FullTime",
        "jobUrl": "https://jobs.ashbyhq.com/example/software-engineer",
        "applyUrl": (
            "https://jobs.ashbyhq.com/example/software-engineer/apply"
        ),
        "address": {
            "postalAddress": {
                "addressLocality": "Bangalore",
                "addressRegion": "Karnataka",
                "addressCountry": "India",
            }
        },
    }
    job.update(overrides)
    return job


@pytest.fixture
def skill_extractor() -> SkillExtractor:
    return SkillExtractor(
        {
            "Java": ["java"],
            "Spring Boot": ["spring boot"],
            "PostgreSQL": ["postgresql", "postgres"],
            "REST APIs": [
                "rest api",
                "rest apis",
                "restful api",
                "restful apis",
            ],
        }
    )


def test_normalize_basic_job(
    skill_extractor: SkillExtractor,
) -> None:
    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(make_job())

    assert job.job_id == "ashby:Example:example/software-engineer"
    assert job.source == "ashby"
    assert job.source_job_id == "example/software-engineer"
    assert job.company == "Example"
    assert job.title == "Software Engineer"

    assert job.description == (
        "Build backend systems using Java, Spring Boot, "
        "PostgreSQL, and REST APIs."
    )

    assert job.location == "Bangalore, India"
    assert job.remote_type == RemoteType.INDIA_REMOTE
    assert job.employment_type == EmploymentType.FULL_TIME
    assert job.experience_level == ExperienceLevel.UNKNOWN

    assert job.skills == [
        "Java",
        "Spring Boot",
        "PostgreSQL",
        "REST APIs",
    ]

    assert job.salary is None

    assert job.posted_at == datetime(
        2026,
        9,
        10,
        10,
        30,
        tzinfo=timezone.utc,
    )

    assert job.updated_at is None

    assert str(job.application_url) == (
        "https://jobs.ashbyhq.com/example/software-engineer/apply"
    )

    assert str(job.source_url) == (
        "https://jobs.ashbyhq.com/example/software-engineer"
    )


def test_normalize_hybrid_job(
    skill_extractor: SkillExtractor,
) -> None:
    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        make_job(
            workplaceType="Hybrid",
            isRemote=False,
        )
    )

    assert job.remote_type == RemoteType.HYBRID


def test_normalize_onsite_job(
    skill_extractor: SkillExtractor,
) -> None:
    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        make_job(
            workplaceType="Onsite",
            isRemote=False,
        )
    )

    assert job.remote_type == RemoteType.ONSITE


def test_remote_job_outside_india_is_unknown(
    skill_extractor: SkillExtractor,
) -> None:
    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        make_job(
            location="Toronto, Canada",
            address={
                "postalAddress": {
                    "addressCountry": "Canada",
                }
            },
        )
    )

    assert job.remote_type == RemoteType.UNKNOWN


@pytest.mark.parametrize(
    ("employment_type", "expected"),
    [
        ("FullTime", EmploymentType.FULL_TIME),
        ("fulltime", EmploymentType.FULL_TIME),
        ("PartTime", EmploymentType.PART_TIME),
        ("parttime", EmploymentType.PART_TIME),
        ("Intern", EmploymentType.INTERNSHIP),
        ("Contract", EmploymentType.CONTRACT),
        ("Temporary", EmploymentType.TEMPORARY),
    ],
)
def test_employment_type_mapping(
    employment_type: str,
    expected: EmploymentType,
    skill_extractor: SkillExtractor,
) -> None:
    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        make_job(employmentType=employment_type)
    )

    assert job.employment_type == expected


def test_description_html_fallback(
    skill_extractor: SkillExtractor,
) -> None:
    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        make_job(
            descriptionPlain="",
            descriptionHtml="<p>Build backend systems using Java.</p>",
        )
    )

    assert job.description == (
        "<p>Build backend systems using Java.</p>"
    )
    assert job.skills == ["Java"]


def test_missing_title_raises_error(
    skill_extractor: SkillExtractor,
) -> None:
    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    with pytest.raises(
        ValueError,
        match="Ashby field 'title' is required",
    ):
        normalizer.normalize(make_job(title=""))


def test_missing_description_raises_error(
    skill_extractor: SkillExtractor,
) -> None:
    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    with pytest.raises(
        ValueError,
        match="descriptionPlain or descriptionHtml",
    ):
        normalizer.normalize(
            make_job(
                descriptionPlain="",
                descriptionHtml="",
            )
        )


def test_missing_apply_url_raises_error(
    skill_extractor: SkillExtractor,
) -> None:
    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    with pytest.raises(
        ValueError,
        match="Ashby field 'applyUrl' is required",
    ):
        normalizer.normalize(
            make_job(applyUrl="")
        )