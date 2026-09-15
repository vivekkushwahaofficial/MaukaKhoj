import pytest

from app.domain.job import Job
from app.normalization.base import JobNormalizer


class ExampleNormalizer(JobNormalizer):
    def normalize(self, raw_job: dict[str, object]) -> Job:
        return Job(
            job_id="example-1",
            source="example",
            source_job_id=str(raw_job["id"]),
            company="Example Company",
            title=str(raw_job["title"]),
            description="Example description",
            application_url="https://example.com/apply",
        )


def test_job_normalizer_converts_raw_job_to_job():
    normalizer = ExampleNormalizer()

    job = normalizer.normalize(
        {
            "id": "123",
            "title": "Backend Developer",
        }
    )

    assert isinstance(job, Job)
    assert job.source_job_id == "123"
    assert job.title == "Backend Developer"


def test_job_normalizer_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        JobNormalizer()
