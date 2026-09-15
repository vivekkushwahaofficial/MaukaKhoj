from datetime import datetime, timezone

from app.domain.education import EducationRequirementStatus
from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    RemoteType,
)
from app.normalization.lever import LeverJobNormalizer


def create_raw_job(**overrides):
    """Create a realistic Lever payload for normalization tests."""

    data = {
        "id": "lever-job-1",
        "text": "Backend Software Engineer",
        "descriptionPlain": ("Build backend services using Java and Spring Boot."),
        "applyUrl": "https://jobs.example.com/backend-1",
        "hostedUrl": "https://jobs.example.com/backend-1",
        "createdAt": 1_757_000_000_000,
        "updatedAt": 1_757_000_100_000,
        "workplaceType": "remote",
        "categories": {
            "location": "India",
            "commitment": "Full-time",
        },
    }

    data.update(overrides)
    return data


def test_normalize_basic_lever_job():
    """Verify the existing Lever-to-canonical mapping remains intact."""

    normalizer = LeverJobNormalizer("Example")

    job = normalizer.normalize(create_raw_job())

    assert job.job_id == "lever:Example:lever-job-1"
    assert job.source == "lever"
    assert job.source_job_id == "lever-job-1"
    assert job.company == "Example"
    assert job.title == "Backend Software Engineer"
    assert job.location == "India"

    assert job.remote_type == RemoteType.INDIA_REMOTE
    assert job.employment_type == EmploymentType.FULL_TIME
    assert job.experience_level == ExperienceLevel.UNKNOWN

    assert str(job.application_url) == "https://jobs.example.com/backend-1"


def test_normalize_extracts_bachelors_degree():
    """Verify Bachelor's degree requirements are extracted."""

    normalizer = LeverJobNormalizer("Example")

    job = normalizer.normalize(
        create_raw_job(
            descriptionPlain=(
                "Requirements: Bachelor's degree in Computer Science "
                "or equivalent experience."
            )
        )
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.REQUIRED
    assert requirement.degree == "Bachelor's degree"
    assert requirement.field == "Computer Science"


def test_normalize_extracts_btech_and_current_student_status():
    """Verify running students and B.Tech requirements are extracted."""

    normalizer = LeverJobNormalizer("Example")

    job = normalizer.normalize(
        create_raw_job(
            descriptionPlain=(
                "Currently enrolled students pursuing a B.Tech "
                "in Computer Science are eligible to apply."
            )
        )
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.REQUIRED
    assert requirement.degree == "B.Tech"
    assert requirement.field == "Computer Science"
    assert requirement.accepts_current_students is True


def test_normalize_extracts_graduation_year():
    """Verify a single graduation year is normalized."""

    normalizer = LeverJobNormalizer("Example")

    job = normalizer.normalize(
        create_raw_job(descriptionPlain=("Candidates graduating in 2027 are eligible."))
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.REQUIRED
    assert requirement.minimum_graduation_year == 2027
    assert requirement.maximum_graduation_year == 2027


def test_normalize_extracts_graduation_range():
    """Verify a graduation-year range is normalized."""

    normalizer = LeverJobNormalizer("Example")

    job = normalizer.normalize(
        create_raw_job(
            descriptionPlain=("Students graduating between 2026 and 2027 " "may apply.")
        )
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.REQUIRED
    assert requirement.minimum_graduation_year == 2026
    assert requirement.maximum_graduation_year == 2027


def test_normalize_no_education_requirement_remains_unknown():
    """Jobs without education information must remain neutral."""

    normalizer = LeverJobNormalizer("Example")

    job = normalizer.normalize(
        create_raw_job(
            descriptionPlain=("Build backend services using Java and Spring Boot.")
        )
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.UNKNOWN
    assert requirement.degree is None
    assert requirement.field is None
    assert requirement.minimum_graduation_year is None
    assert requirement.maximum_graduation_year is None
    assert requirement.accepts_current_students is None


def test_normalize_explicit_no_degree_requirement():
    """Verify explicit absence of a degree requirement is preserved."""

    normalizer = LeverJobNormalizer("Example")

    job = normalizer.normalize(
        create_raw_job(
            descriptionPlain=(
                "No degree required. "
                "Practical software development experience is valued."
            )
        )
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.NOT_REQUIRED


def test_normalize_falls_back_to_html_description():
    """Verify the existing description fallback still works."""

    normalizer = LeverJobNormalizer("Example")

    job = normalizer.normalize(
        create_raw_job(
            descriptionPlain=None,
            description=("Bachelor's degree in Computer Science required."),
        )
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.REQUIRED
    assert requirement.degree == "Bachelor's degree"
    assert requirement.field == "Computer Science"


def test_normalize_preserves_timestamps():
    """Verify Lever millisecond timestamps are converted to UTC."""

    normalizer = LeverJobNormalizer("Example")

    job = normalizer.normalize(create_raw_job())

    assert job.posted_at == datetime.fromtimestamp(
        1_757_000_000_000 / 1000,
        tz=timezone.utc,
    )

    assert job.updated_at == datetime.fromtimestamp(
        1_757_000_100_000 / 1000,
        tz=timezone.utc,
    )
