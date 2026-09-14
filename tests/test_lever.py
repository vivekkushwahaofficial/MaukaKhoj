from app.sources.lever import LeverAdapter


class FakeHttpClient:
    def get_json(self, url: str) -> object:
        assert url == "https://api.lever.co/v0/postings/example?mode=json"

        return [
            {
                "id": "lever-123",
                "text": "Backend Developer",
                "categories": {
                    "location": "India",
                    "commitment": "Full-time",
                },
            }
        ]


def test_lever_adapter_exposes_source_name():
    adapter = LeverAdapter(
        account_name="example",
        http_client=FakeHttpClient(),
    )

    assert adapter.source_name == "lever"


def test_lever_adapter_uses_account_name_and_returns_raw_jobs():
    adapter = LeverAdapter(
        account_name="example",
        http_client=FakeHttpClient(),
    )

    jobs = adapter.fetch_jobs()

    assert jobs == [
        {
            "id": "lever-123",
            "text": "Backend Developer",
            "categories": {
                "location": "India",
                "commitment": "Full-time",
            },
        }
    ]
