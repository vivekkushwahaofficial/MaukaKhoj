from typing import Any

from app.sources.base import JobSourceAdapter
from app.sources.http_client import HttpClient


class LeverAdapter(JobSourceAdapter):
    """Fetch published job postings from a Lever account."""

    def __init__(
        self,
        account_name: str,
        http_client: HttpClient,
    ) -> None:
        self._account_name = account_name
        self._http_client = http_client

    @property
    def source_name(self) -> str:
        return "lever"

    def fetch_jobs(self) -> list[dict[str, Any]]:
        """Fetch raw published job postings from Lever."""
        url = f"https://api.lever.co/v0/postings/{self._account_name}" f"?mode=json"

        response = self._http_client.get_json(url)

        if not isinstance(response, list):
            raise ValueError("Lever response must be a JSON array.")

        return response
