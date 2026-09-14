from datetime import datetime, timezone

import pytest

from app.domain.job import EmploymentType, ExperienceLevel, Job, RemoteType
from app.domain.profile import Education, Experience, Profile
from app.matching.job import CanonicalJobProfileMatcher


@pytest.fixture
def matcher() -> CanonicalJobProfileMatcher:
    return CanonicalJobProfileMatcher()


def create_job(**overrides) -> Job:
    data = {
        "job_id": "job-1",
        "source": "test",
        "source_job_id": "source-1",
        "company": "Example",
        "title": "Java Backend Developer",
        "description": "Backend development using Java and Spring Boot.",
        "location": "India",
        "remote_type": RemoteType.INDIA_REMOTE,
        "employment_type": EmploymentType.FULL_TIME,
        "experience_level": ExperienceLevel.ENTRY_LEVEL,
        "skills": ["Java", "Spring Boot", "PostgreSQL"],
        "posted_at": datetime.now(timezone.utc),
        "application_url": "https://example.com/jobs/1",
    }

    data.update(overrides)
    return Job(**data)


def create_profile(**overrides) -> Profile:
    data = {
        "name": "Candidate",
        "target_titles": ["Backend Developer"],
        "skills": ["Java", "Spring Boot", "Docker"],
        "experience": Experience(
            years=1.0,
            current_title="Java Developer",
        ),
        "education": Education(
            degree="B.Tech",
            field="Computer Science",
        ),
        "locations": ["India"],
        "remote_preferences": ["INDIA_REMOTE"],
        "employment_preferences": ["FULL_TIME"],
        "domains": ["Backend"],
    }

    data.update(overrides)
    return Profile(**data)


def test_role_matches_target_title(matcher):
    result = matcher.match(
        create_job(),
        create_profile(),
    )

    assert result.role.matched is True
    assert result.role.matched_values == ("Backend Developer",)


def test_role_mismatch_is_reported(matcher):
    result = matcher.match(
        create_job(title="Senior Data Scientist"),
        create_profile(),
    )

    assert result.role.matched is False
    assert result.role.missing_values == ("Backend Developer",)


def test_skills_report_matched_and_missing_skills(matcher):
    result = matcher.match(
        create_job(),
        create_profile(),
    )

    assert result.skills.matched is True
    assert result.skills.matched_values == (
        "Java",
        "Spring Boot",
    )
    assert result.skills.missing_values == ("Docker",)


def test_empty_profile_skills_are_unknown(matcher):
    result = matcher.match(
        create_job(),
        create_profile(skills=[]),
    )

    assert result.skills.matched is None


def test_unknown_experience_level_is_unknown(matcher):
    result = matcher.match(
        create_job(experience_level=ExperienceLevel.UNKNOWN),
        create_profile(),
    )

    assert result.experience.matched is None


def test_location_matches_profile_location(matcher):
    result = matcher.match(
        create_job(location="India"),
        create_profile(),
    )

    assert result.location.matched is True
    assert result.location.matched_values == ("India",)


def test_missing_job_location_is_unknown(matcher):
    result = matcher.match(
        create_job(location=None),
        create_profile(),
    )

    assert result.location.matched is None


def test_remote_preference_matches_job_remote_type(matcher):
    result = matcher.match(
        create_job(remote_type=RemoteType.INDIA_REMOTE),
        create_profile(),
    )

    assert result.remote.matched is True


def test_unknown_remote_type_is_unknown(matcher):
    result = matcher.match(
        create_job(remote_type=RemoteType.UNKNOWN),
        create_profile(),
    )

    assert result.remote.matched is None


def test_employment_preference_matches(matcher):
    result = matcher.match(
        create_job(employment_type=EmploymentType.FULL_TIME),
        create_profile(),
    )

    assert result.employment.matched is True


def test_employment_preference_mismatch_is_reported(matcher):
    result = matcher.match(
        create_job(employment_type=EmploymentType.INTERNSHIP),
        create_profile(),
    )

    assert result.employment.matched is False


def test_domain_is_detected_in_job_information(matcher):
    result = matcher.match(
        create_job(
            title="Backend Developer",
            description="Build backend APIs and services.",
        ),
        create_profile(domains=["Backend"]),
    )

    assert result.domain.matched is True
    assert result.domain.matched_values == ("Backend",)


def test_missing_domain_information_is_reported(matcher):
    result = matcher.match(
        create_job(
            title="Frontend Developer",
            description="Build user interfaces.",
            skills=["React", "JavaScript"],
        ),
        create_profile(domains=["Backend"]),
    )

    assert result.domain.matched is False


def test_education_is_unknown_when_job_has_no_education_requirements(matcher):
    result = matcher.match(
        create_job(),
        create_profile(),
    )

    assert result.education.matched is None


def test_no_preferences_produce_unknown_dimensions(matcher):
    result = matcher.match(
        create_job(),
        Profile(name="Candidate"),
    )

    assert result.role.matched is None
    assert result.skills.matched is None
    assert result.experience.matched is None
    assert result.education.matched is None
    assert result.location.matched is None
    assert result.remote.matched is None
    assert result.employment.matched is None
    assert result.domain.matched is None
