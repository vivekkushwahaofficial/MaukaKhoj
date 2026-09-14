import pytest

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    RemoteType,
)
from app.normalization.lever import LeverJobNormalizer


@pytest.fixture
def normalizer():
    return LeverJobNormalizer("gohighlevel")


@pytest.fixture
def raw_lever_job():
    return {
        "id": "lever-123",
        "text": "Backend Developer",
        "descriptionPlain": "Build backend services.",
        "categories": {
            "location": "India",
            "commitment": "Full-time",
        },
        "workplaceType": "remote",
        "createdAt": 1784650515708,
        "updatedAt": 1784650515708,
        "hostedUrl": "https://jobs.lever.co/gohighlevel/lever-123",
        "applyUrl": "https://jobs.lever.co/gohighlevel/lever-123/apply",
    }


def test_normalizer_converts_lever_job(normalizer, raw_lever_job):
    job = normalizer.normalize(raw_lever_job)

    assert job.job_id == "lever:gohighlevel:lever-123"
    assert job.source == "lever"
    assert job.source_job_id == "lever-123"
    assert job.company == "gohighlevel"
    assert job.title == "Backend Developer"
    assert job.description == "Build backend services."
    assert job.location == "India"

    assert job.remote_type == RemoteType.INDIA_REMOTE
    assert job.employment_type == EmploymentType.FULL_TIME
    assert job.experience_level == ExperienceLevel.UNKNOWN
    assert job.skills == []

    assert str(job.application_url) == (
        "https://jobs.lever.co/gohighlevel/lever-123/apply"
    )
    assert str(job.source_url) == ("https://jobs.lever.co/gohighlevel/lever-123")


def test_normalizer_handles_missing_optional_fields(normalizer):
    raw_job = {
        "id": "lever-456",
        "text": "Software Engineer",
        "descriptionPlain": "Build software.",
        "applyUrl": "https://example.com/apply",
    }

    job = normalizer.normalize(raw_job)

    assert job.location is None
    assert job.remote_type == RemoteType.UNKNOWN
    assert job.employment_type == EmploymentType.UNKNOWN
    assert job.experience_level == ExperienceLevel.UNKNOWN
    assert job.skills == []
    assert job.posted_at is None
    assert job.updated_at is None
    assert job.source_url is None


def test_normalizer_rejects_missing_required_field(normalizer):
    raw_job = {
        "id": "lever-789",
        "text": "Software Engineer",
        "descriptionPlain": "Build software.",
    }

    with pytest.raises(
        ValueError,
        match="Lever field 'applyUrl' is required",
    ):
        normalizer.normalize(raw_job)


def test_normalizer_rejects_invalid_categories(normalizer):
    raw_job = {
        "id": "lever-789",
        "text": "Software Engineer",
        "descriptionPlain": "Build software.",
        "categories": "India",
        "applyUrl": "https://example.com/apply",
    }

    with pytest.raises(
        ValueError,
        match="Lever categories must be an object",
    ):
        normalizer.normalize(raw_job)
