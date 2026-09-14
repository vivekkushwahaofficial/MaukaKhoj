import httpx


class HttpClient:
    """Small wrapper around HTTP requests used by source adapters."""

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._client = httpx.Client(timeout=timeout_seconds)

    def get_json(self, url: str) -> object:
        """Send a GET request and return the decoded JSON response."""
        response = self._client.get(url)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()