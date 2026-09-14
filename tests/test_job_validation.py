from datetime import datetime, timezone

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.validation.job import CanonicalJobValidator
from app.validation.models import ValidationSeverity


def make_job(**overrides: object) -> Job:
    data = {
        "job_id": "job-1",
        "source": "lever",
        "source_job_id": "source-1",
        "company": "Test Company",
        "title": "Backend Engineer",
        "description": "Build backend systems.",
        "location": "Bangalore, India",
        "remote_type": RemoteType.INDIA_REMOTE,
        "employment_type": EmploymentType.FULL_TIME,
        "experience_level": ExperienceLevel.ENTRY_LEVEL,
        "skills": ["Java", "Spring Boot"],
        "salary": None,
        "posted_at": datetime(2026, 9, 10, tzinfo=timezone.utc),
        "updated_at": None,
        "application_url": "https://example.com/apply",
        "company_url": None,
        "source_url": "https://example.com/job",
    }

    data.update(overrides)

    return Job(**data)


def test_valid_job_has_no_issues() -> None:
    validator = CanonicalJobValidator()

    result = validator.validate(make_job())

    assert result.is_valid is True
    assert result.errors == ()
    assert result.warnings == ()
    assert result.issues == ()


def test_missing_source_job_id_creates_warning() -> None:
    validator = CanonicalJobValidator()

    result = validator.validate(
        make_job(source_job_id=None),
    )

    assert result.is_valid is True
    assert len(result.warnings) == 1
    assert result.warnings[0].severity == ValidationSeverity.WARNING
    assert result.warnings[0].code == "MISSING_SOURCE_JOB_ID"


def test_unknown_remote_type_creates_warning() -> None:
    validator = CanonicalJobValidator()

    result = validator.validate(
        make_job(remote_type=RemoteType.UNKNOWN),
    )

    assert result.is_valid is True
    assert result.warnings[0].code == "UNKNOWN_REMOTE_TYPE"


def test_unknown_employment_type_creates_warning() -> None:
    validator = CanonicalJobValidator()

    result = validator.validate(
        make_job(employment_type=EmploymentType.UNKNOWN),
    )

    assert result.is_valid is True
    assert result.warnings[0].code == "UNKNOWN_EMPLOYMENT_TYPE"


def test_unknown_experience_level_creates_warning() -> None:
    validator = CanonicalJobValidator()

    result = validator.validate(
        make_job(experience_level=ExperienceLevel.UNKNOWN),
    )

    assert result.is_valid is True
    assert result.warnings[0].code == "UNKNOWN_EXPERIENCE_LEVEL"


def test_missing_location_creates_warning() -> None:
    validator = CanonicalJobValidator()

    result = validator.validate(
        make_job(location=None),
    )

    assert result.is_valid is True
    assert result.warnings[0].code == "MISSING_LOCATION"


def test_missing_posted_at_creates_warning() -> None:
    validator = CanonicalJobValidator()

    result = validator.validate(
        make_job(posted_at=None),
    )

    assert result.is_valid is True
    assert result.warnings[0].code == "MISSING_POSTED_AT"


def test_multiple_warnings_are_collected() -> None:
    validator = CanonicalJobValidator()

    result = validator.validate(
        make_job(
            source_job_id=None,
            remote_type=RemoteType.UNKNOWN,
            employment_type=EmploymentType.UNKNOWN,
            experience_level=ExperienceLevel.UNKNOWN,
            location=None,
            posted_at=None,
        ),
    )

    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 6
