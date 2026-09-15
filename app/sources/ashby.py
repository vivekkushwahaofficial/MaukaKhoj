from typing import Any

from app.sources.base import JobSourceAdapter
from app.sources.http_client import HttpClient


class AshbyAdapter(JobSourceAdapter):
    """Fetch published job postings from an Ashby job board."""

    def __init__(
        self,
        job_board_name: str,
        http_client: HttpClient,
    ) -> None:
        if not job_board_name.strip():
            raise ValueError("Ashby job board name cannot be empty.")

        self._job_board_name = job_board_name.strip()
        self._http_client = http_client

    @property
    def source_name(self) -> str:
        return "ashby"

    @property
    def source_id(self) -> str:
        return f"ashby:{self._job_board_name}"

    def fetch_jobs(self) -> list[dict[str, Any]]:
        """Fetch raw published job postings from Ashby."""

        url = "https://api.ashbyhq.com/" f"posting-api/job-board/{self._job_board_name}"

        response = self._http_client.get_json(url)

        if not isinstance(response, dict):
            raise ValueError("Ashby response must be a JSON object.")

        jobs = response.get("jobs")

        if not isinstance(jobs, list):
            raise ValueError("Ashby response must contain a jobs array.")

        if not all(isinstance(job, dict) for job in jobs):
            raise ValueError("Ashby jobs must contain JSON objects.")

        return jobs
