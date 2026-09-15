from datetime import datetime, timezone

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)


def test_job_can_be_created():
    job = Job(
        job_id="job-001",
        source="test",
        source_job_id="123",
        company="Example Corp",
        title="Backend Developer",
        description="Build backend services.",
        location="India",
        remote_type=RemoteType.INDIA_REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY_LEVEL,
        skills=["Python", "FastAPI"],
        posted_at=datetime.now(timezone.utc),
        application_url="https://example.com/jobs/123",
    )

    assert job.job_id == "job-001"
    assert job.company == "Example Corp"
    assert job.remote_type == RemoteType.INDIA_REMOTE
    assert "Python" in job.skills


def test_job_defaults_unknown_values():
    job = Job(
        job_id="job-002",
        source="test",
        company="Example Corp",
        title="Software Engineer",
        description="Software engineering role.",
        application_url="https://example.com/jobs/456",
    )

    assert job.remote_type == RemoteType.UNKNOWN
    assert job.employment_type == EmploymentType.UNKNOWN
    assert job.experience_level == ExperienceLevel.UNKNOWN


def test_job_rejects_empty_required_fields():
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        Job(
            job_id="",
            source="test",
            company="Example Corp",
            title="Software Engineer",
            description="Software engineering role.",
            application_url="https://example.com/jobs/456",
        )
