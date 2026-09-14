import pytest

from app.sources.base import JobSourceAdapter


class ExampleJobSource(JobSourceAdapter):
    @property
    def source_name(self) -> str:
        return "example"

    def fetch_jobs(self) -> list[dict[str, object]]:
        return [
            {
                "id": "123",
                "title": "Backend Developer",
            }
        ]


def test_job_source_adapter_exposes_source_name():
    adapter = ExampleJobSource()

    assert adapter.source_name == "example"


def test_job_source_adapter_fetches_raw_jobs():
    adapter = ExampleJobSource()

    jobs = adapter.fetch_jobs()

    assert jobs == [
        {
            "id": "123",
            "title": "Backend Developer",
        }
    ]


def test_job_source_adapter_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        JobSourceAdapter()
