from datetime import datetime, timezone

import pytest

from app.domain.job import EmploymentType, RemoteType
from app.normalization.ashby import AshbyJobNormalizer


def make_job(**overrides: object) -> dict:
    job = {
        "title": "Software Engineer",
        "location": "Bangalore, India",
        "isRemote": True,
        "workplaceType": "Remote",
        "descriptionPlain": "Build backend systems.",
        "publishedAt": "2026-09-10T10:30:00.000+00:00",
        "employmentType": "FullTime",
        "jobUrl": "https://jobs.ashbyhq.com/example/software-engineer",
        "applyUrl": "https://jobs.ashbyhq.com/example/software-engineer/apply",
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


def test_normalizes_basic_ashby_job() -> None:
    normalizer = AshbyJobNormalizer("Example")

    job = normalizer.normalize(make_job())

    assert job.job_id == ("ashby:Example:example/software-engineer")
    assert job.source == "ashby"
    assert job.source_job_id == "example/software-engineer"
    assert job.company == "Example"
    assert job.title == "Software Engineer"
    assert job.description == "Build backend systems."
    assert job.location == "Bangalore, India"
    assert job.remote_type == RemoteType.INDIA_REMOTE
    assert job.employment_type == EmploymentType.FULL_TIME
    assert str(job.application_url).endswith("/apply")
    assert str(job.source_url).endswith("/software-engineer")
    assert job.posted_at == datetime(
        2026,
        9,
        10,
        10,
        30,
        tzinfo=timezone.utc,
    )


def test_maps_hybrid() -> None:
    normalizer = AshbyJobNormalizer("Example")

    job = normalizer.normalize(
        make_job(
            isRemote=False,
            workplaceType="Hybrid",
        )
    )

    assert job.remote_type == RemoteType.HYBRID


def test_maps_onsite() -> None:
    normalizer = AshbyJobNormalizer("Example")

    job = normalizer.normalize(
        make_job(
            isRemote=False,
            workplaceType="OnSite",
        )
    )

    assert job.remote_type == RemoteType.ONSITE


def test_remote_outside_india_is_unknown_for_now() -> None:
    normalizer = AshbyJobNormalizer("Example")

    job = normalizer.normalize(
        make_job(
            location="New York, USA",
            address={
                "postalAddress": {
                    "addressCountry": "USA",
                }
            },
        )
    )

    assert job.remote_type == RemoteType.UNKNOWN


def test_maps_employment_types() -> None:
    normalizer = AshbyJobNormalizer("Example")

    assert (
        normalizer.normalize(make_job(employmentType="Intern")).employment_type
        == EmploymentType.INTERNSHIP
    )

    assert (
        normalizer.normalize(make_job(employmentType="Contract")).employment_type
        == EmploymentType.CONTRACT
    )

    assert (
        normalizer.normalize(make_job(employmentType="PartTime")).employment_type
        == EmploymentType.PART_TIME
    )


def test_description_html_is_fallback() -> None:
    normalizer = AshbyJobNormalizer("Example")

    job = normalizer.normalize(
        make_job(
            descriptionPlain="",
            descriptionHtml="<p>Build great software.</p>",
        )
    )

    assert job.description == "<p>Build great software.</p>"


def test_missing_title_is_rejected() -> None:
    normalizer = AshbyJobNormalizer("Example")

    with pytest.raises(ValueError, match="title"):
        normalizer.normalize(make_job(title=""))


def test_missing_description_is_rejected() -> None:
    normalizer = AshbyJobNormalizer("Example")

    with pytest.raises(ValueError, match="description"):
        normalizer.normalize(
            make_job(
                descriptionPlain="",
                descriptionHtml="",
            )
        )


def test_missing_apply_url_is_rejected() -> None:
    normalizer = AshbyJobNormalizer("Example")

    with pytest.raises(ValueError, match="applyUrl"):
        normalizer.normalize(make_job(applyUrl=""))
