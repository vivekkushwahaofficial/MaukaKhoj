import httpx
import pytest

from app.sources.http_client import HttpClient


def test_get_json_returns_decoded_json(monkeypatch):
    client = HttpClient()

    def fake_get(url: str):
        return httpx.Response(
            status_code=200,
            json={"jobs": [{"id": "123"}]},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(client._client, "get", fake_get)

    result = client.get_json("https://example.com/jobs")

    assert result == {"jobs": [{"id": "123"}]}

    client.close()


def test_get_json_raises_for_http_error(monkeypatch):
    client = HttpClient()

    def fake_get(url: str):
        return httpx.Response(
            status_code=500,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(client._client, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        client.get_json("https://example.com/jobs")

    client.close()


def test_close_closes_http_client():
    client = HttpClient()

    assert not client._client.is_closed

    client.close()

    assert client._client.is_closed