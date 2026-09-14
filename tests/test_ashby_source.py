import pytest

from app.sources.ashby import AshbyAdapter


class FakeHttpClient:
    def __init__(self, response: object) -> None:
        self.response = response
        self.requested_url: str | None = None

    def get_json(self, url: str) -> object:
        self.requested_url = url
        return self.response


def test_fetch_jobs_returns_jobs() -> None:
    client = FakeHttpClient(
        {
            "apiVersion": "1",
            "jobs": [
                {
                    "title": "Software Engineer",
                    "location": "India",
                }
            ],
        }
    )

    adapter = AshbyAdapter("ExampleCompany", client)

    jobs = adapter.fetch_jobs()

    assert jobs == [
        {
            "title": "Software Engineer",
            "location": "India",
        }
    ]

    assert (
        client.requested_url == "https://api.ashbyhq.com/"
        "posting-api/job-board/ExampleCompany"
    )


def test_source_name_is_ashby() -> None:
    client = FakeHttpClient({"apiVersion": "1", "jobs": []})

    adapter = AshbyAdapter("ExampleCompany", client)

    assert adapter.source_name == "ashby"


def test_empty_job_board_name_is_rejected() -> None:
    client = FakeHttpClient({"apiVersion": "1", "jobs": []})

    with pytest.raises(ValueError, match="job board name"):
        AshbyAdapter("   ", client)


def test_invalid_response_type_is_rejected() -> None:
    client = FakeHttpClient([])

    adapter = AshbyAdapter("ExampleCompany", client)

    with pytest.raises(ValueError, match="JSON object"):
        adapter.fetch_jobs()


def test_missing_jobs_field_is_rejected() -> None:
    client = FakeHttpClient({"apiVersion": "1"})

    adapter = AshbyAdapter("ExampleCompany", client)

    with pytest.raises(ValueError, match="jobs array"):
        adapter.fetch_jobs()


def test_invalid_job_item_is_rejected() -> None:
    client = FakeHttpClient(
        {
            "apiVersion": "1",
            "jobs": ["invalid"],
        }
    )

    adapter = AshbyAdapter("ExampleCompany", client)

    with pytest.raises(ValueError, match="JSON objects"):
        adapter.fetch_jobs()
