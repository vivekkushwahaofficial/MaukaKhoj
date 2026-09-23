from datetime import datetime

import pytest

from app.domain.education import EducationRequirementStatus
from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    RemoteType,
)
from app.normalization.ashby import AshbyJobNormalizer
from app.normalization.skills import SkillExtractor


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


def create_raw_job(**overrides):
    """Create a realistic Ashby posting payload for tests."""

    data = {
        "title": "Backend Software Engineer",
        "descriptionPlain": (
            "Build backend services using Java and Spring Boot, "
            "PostgreSQL, and REST APIs."
        ),
        "descriptionHtml": (
            "<p>Build backend services using Java and Spring Boot, "
            "PostgreSQL, and REST APIs.</p>"
        ),
        "applyUrl": "https://jobs.example.com/apply/backend-1",
        "jobUrl": "https://jobs.example.com/backend-1",
        "location": "India",
        "workplaceType": "remote",
        "isRemote": True,
        "employmentType": "fulltime",
        "publishedAt": "2026-09-15T10:00:00Z",
        "address": {
            "postalAddress": {
                "addressCountry": "India",
            }
        },
        "compensation": {
            "scrapeableCompensationSalarySummary": ("₹8,00,000 - ₹12,00,000")
        },
    }

    data.update(overrides)
    return data


def test_normalize_basic_ashby_job(
    skill_extractor: SkillExtractor,
):
    """Verify the existing Ashby-to-canonical mapping."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(create_raw_job())

    assert job.job_id == "ashby:Example:backend-1"
    assert job.source == "ashby"
    assert job.source_job_id == "backend-1"
    assert job.company == "Example"
    assert job.title == "Backend Software Engineer"
    assert job.location == "India"

    assert job.remote_type == RemoteType.INDIA_REMOTE
    assert job.employment_type == EmploymentType.FULL_TIME

    assert job.skills == [
        "Java",
        "Spring Boot",
        "PostgreSQL",
        "REST APIs",
    ]

    assert str(job.application_url) == ("https://jobs.example.com/apply/backend-1")

    assert job.salary == "₹8,00,000 - ₹12,00,000"


def test_normalize_extracts_bachelors_degree(
    skill_extractor: SkillExtractor,
):
    """Verify Bachelor's degree requirements are extracted."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

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


def test_normalize_extracts_btech_and_current_student_status(
    skill_extractor: SkillExtractor,
):
    """Verify B.Tech and current-student requirements are extracted."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

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


def test_normalize_extracts_graduation_year(
    skill_extractor: SkillExtractor,
):
    """Verify a single graduation year is extracted."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        create_raw_job(descriptionPlain=("Candidates graduating in 2027 are eligible."))
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.REQUIRED
    assert requirement.minimum_graduation_year == 2027
    assert requirement.maximum_graduation_year == 2027


def test_normalize_extracts_graduation_range(
    skill_extractor: SkillExtractor,
):
    """Verify a graduation-year range is extracted."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        create_raw_job(
            descriptionPlain=("Students graduating between 2026 and 2027 may apply.")
        )
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.REQUIRED
    assert requirement.minimum_graduation_year == 2026
    assert requirement.maximum_graduation_year == 2027


def test_normalize_class_of_year(
    skill_extractor: SkillExtractor,
):
    """Verify class-of graduation wording is extracted."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        create_raw_job(
            descriptionPlain=(
                "This internship is intended for students " "from the class of 2027."
            )
        )
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.REQUIRED
    assert requirement.minimum_graduation_year == 2027
    assert requirement.maximum_graduation_year == 2027


def test_normalize_no_education_requirement_remains_unknown(
    skill_extractor: SkillExtractor,
):
    """Jobs without education information remain neutral."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

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


def test_normalize_explicit_no_degree_requirement(
    skill_extractor: SkillExtractor,
):
    """Verify an explicit no-degree rule is preserved."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

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


def test_normalize_falls_back_to_html_description(
    skill_extractor: SkillExtractor,
):
    """Verify the existing HTML description fallback."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        create_raw_job(
            descriptionPlain=None,
            descriptionHtml=("Bachelor's degree in Computer Science required."),
        )
    )

    requirement = job.education_requirement

    assert requirement.status == EducationRequirementStatus.REQUIRED
    assert requirement.degree == "Bachelor's degree"
    assert requirement.field == "Computer Science"


def test_normalize_remote_india(
    skill_extractor: SkillExtractor,
):
    """Verify remote jobs with an India address become INDIA_REMOTE."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        create_raw_job(
            isRemote=True,
            workplaceType="remote",
            location="India",
        )
    )

    assert job.remote_type == RemoteType.INDIA_REMOTE


def test_normalize_hybrid_job(
    skill_extractor: SkillExtractor,
):
    """Verify Ashby hybrid workplace mapping."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        create_raw_job(
            isRemote=False,
            workplaceType="hybrid",
        )
    )

    assert job.remote_type == RemoteType.HYBRID


def test_normalize_onsite_job(
    skill_extractor: SkillExtractor,
):
    """Verify Ashby onsite workplace mapping."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(
        create_raw_job(
            isRemote=False,
            workplaceType="onsite",
        )
    )

    assert job.remote_type == RemoteType.ONSITE


def test_normalize_timestamp(
    skill_extractor: SkillExtractor,
):
    """Verify Ashby's ISO timestamp becomes a datetime."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(create_raw_job())

    assert job.posted_at == datetime.fromisoformat("2026-09-15T10:00:00+00:00")


def test_normalize_salary_missing(
    skill_extractor: SkillExtractor,
):
    """Missing compensation should remain None."""

    normalizer = AshbyJobNormalizer(
        "Example",
        skill_extractor=skill_extractor,
    )

    job = normalizer.normalize(create_raw_job(compensation=None))

    assert job.salary is None
