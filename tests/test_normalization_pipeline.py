import pytest
from datetime import datetime, timezone

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)

from app.normalization.ashby import AshbyJobNormalizer
from app.normalization.base import JobNormalizer
from app.normalization.pipeline import NormalizationPipeline
from app.normalization.registry import NormalizationRegistry
from app.normalization.skills import SkillExtractor


class FakeNormalizer(JobNormalizer):
    """Test normalizer that creates a minimal canonical Job."""

    def normalize(self, raw_job: dict) -> Job:
        return Job(
            job_id=raw_job["id"],
            source="fake",
            source_job_id=raw_job["id"],
            company="Test Company",
            title=raw_job["title"],
            description="Test description",
            location="India",
            remote_type=RemoteType.INDIA_REMOTE,
            employment_type=EmploymentType.FULL_TIME,
            experience_level=ExperienceLevel.ENTRY_LEVEL,
            application_url="https://example.com/apply",
            posted_at=datetime.now(timezone.utc),
        )


def create_pipeline() -> NormalizationPipeline:
    registry = NormalizationRegistry()
    registry.register("fake", FakeNormalizer())

    return NormalizationPipeline(registry)


def test_pipeline_normalizes_multiple_jobs() -> None:
    pipeline = create_pipeline()

    raw_jobs = [
        {"id": "1", "title": "Java Developer"},
        {"id": "2", "title": "Backend Developer"},
    ]

    jobs = pipeline.normalize("fake", raw_jobs)

    assert len(jobs) == 2
    assert jobs[0].job_id == "1"
    assert jobs[0].title == "Java Developer"
    assert jobs[1].job_id == "2"
    assert jobs[1].title == "Backend Developer"


def test_pipeline_returns_empty_list_for_empty_input() -> None:
    pipeline = create_pipeline()

    jobs = pipeline.normalize("fake", [])

    assert jobs == []


def test_pipeline_rejects_unknown_source() -> None:
    pipeline = create_pipeline()

    with pytest.raises(
        ValueError,
        match="No job normalizer registered",
    ):
        pipeline.normalize(
            "unknown",
            [{"id": "1", "title": "Developer"}],
        )


def test_pipeline_normalizes_ashby_jobs() -> None:
    skill_extractor = SkillExtractor(
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

    registry = NormalizationRegistry()
    registry.register(
        "ashby",
        AshbyJobNormalizer(
            "Example",
            skill_extractor=skill_extractor,
        ),
    )

    pipeline = NormalizationPipeline(registry)

    raw_jobs = [
        {
            "title": "Backend Engineer",
            "location": "Bangalore, India",
            "isRemote": True,
            "workplaceType": "Remote",
            "descriptionPlain": "Build backend systems.",
            "publishedAt": "2026-09-10T10:30:00.000+00:00",
            "employmentType": "FullTime",
            "jobUrl": (
                "https://jobs.ashbyhq.com/"
                "example/backend-engineer"
            ),
            "applyUrl": (
                "https://jobs.ashbyhq.com/"
                "example/backend-engineer/apply"
            ),
            "address": {
                "postalAddress": {
                    "addressCountry": "India",
                }
            },
        }
    ]

    jobs = pipeline.normalize("ashby", raw_jobs)

    assert len(jobs) == 1
    assert jobs[0].source == "ashby"
    assert jobs[0].company == "Example"
    assert jobs[0].title == "Backend Engineer"
    assert jobs[0].remote_type == RemoteType.INDIA_REMOTE