from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.normalization.base import JobNormalizer


class AshbyJobNormalizer(JobNormalizer):
    """Normalize a raw Ashby posting into a canonical Job."""

    def __init__(self, job_board_name: str) -> None:
        if not job_board_name.strip():
            raise ValueError("Ashby job board name cannot be empty.")

        self._job_board_name = job_board_name.strip()

    def normalize(self, raw_job: dict[str, Any]) -> Job:
        """Convert one raw Ashby posting into a canonical Job."""

        title = self._required_string(raw_job, "title")
        description = self._get_description(raw_job)
        application_url = self._required_string(raw_job, "applyUrl")

        source_job_id = self._build_source_job_id(
            raw_job,
            application_url,
        )

        location = self._optional_string(raw_job.get("location"))
        workplace_type = self._optional_string(raw_job.get("workplaceType"))

        return Job(
            job_id=f"ashby:{self._job_board_name}:{source_job_id}",
            source="ashby",
            source_job_id=source_job_id,
            company=self._job_board_name,
            title=title,
            description=description,
            location=location,
            remote_type=self._map_remote_type(
                raw_job.get("isRemote"),
                workplace_type,
                raw_job.get("address"),
            ),
            employment_type=self._map_employment_type(raw_job.get("employmentType")),
            experience_level=ExperienceLevel.UNKNOWN,
            skills=[],
            salary=self._get_salary(raw_job),
            posted_at=self._parse_timestamp(raw_job.get("publishedAt")),
            updated_at=None,
            application_url=application_url,
            company_url=None,
            source_url=self._optional_string(raw_job.get("jobUrl")),
        )

    @staticmethod
    def _required_string(
        raw_job: dict[str, Any],
        field: str,
    ) -> str:
        value = raw_job.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Ashby field '{field}' is required.")

        return value.strip()

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()

        return None

    @staticmethod
    def _get_description(
        raw_job: dict[str, Any],
    ) -> str:
        plain_description = raw_job.get("descriptionPlain")

        if isinstance(plain_description, str) and plain_description.strip():
            return plain_description.strip()

        description_html = raw_job.get("descriptionHtml")

        if isinstance(description_html, str) and description_html.strip():
            return description_html.strip()

        raise ValueError(
            "Ashby job must contain a non-empty " "descriptionPlain or descriptionHtml."
        )

    @staticmethod
    def _build_source_job_id(
        raw_job: dict[str, Any],
        application_url: str,
    ) -> str:
        """
        Build a stable identifier from the public Ashby posting data.

        The public Job Postings API does not document a job ID in its
        response, so use the Ashby job URL as the fallback identity.
        """

        job_url = raw_job.get("jobUrl")

        if isinstance(job_url, str) and job_url.strip():
            parsed = urlparse(job_url.strip())

            if parsed.path:
                return parsed.path.strip("/")

        apply_url = urlparse(application_url)

        if apply_url.path:
            return apply_url.path.strip("/")

        raise ValueError("Ashby job must contain a usable jobUrl or applyUrl.")

    @staticmethod
    def _map_remote_type(
        is_remote: Any,
        workplace_type: str | None,
        address: Any,
    ) -> RemoteType:
        normalized_workplace = workplace_type.lower() if workplace_type else ""

        if normalized_workplace == "hybrid":
            return RemoteType.HYBRID

        if normalized_workplace == "onsite":
            return RemoteType.ONSITE

        if normalized_workplace == "remote" or is_remote is True:
            country = AshbyJobNormalizer._get_country(address)

            if country and country.lower() == "india":
                return RemoteType.INDIA_REMOTE

            return RemoteType.UNKNOWN

        return RemoteType.UNKNOWN

    @staticmethod
    def _get_country(address: Any) -> str | None:
        if not isinstance(address, dict):
            return None

        postal_address = address.get("postalAddress")

        if not isinstance(postal_address, dict):
            return None

        country = postal_address.get("addressCountry")

        if isinstance(country, str) and country.strip():
            return country.strip()

        return None

    @staticmethod
    def _map_employment_type(
        employment_type: Any,
    ) -> EmploymentType:
        if not isinstance(employment_type, str):
            return EmploymentType.UNKNOWN

        normalized = employment_type.strip().lower()

        mapping = {
            "fulltime": EmploymentType.FULL_TIME,
            "parttime": EmploymentType.PART_TIME,
            "intern": EmploymentType.INTERNSHIP,
            "contract": EmploymentType.CONTRACT,
            "temporary": EmploymentType.TEMPORARY,
        }

        return mapping.get(
            normalized,
            EmploymentType.UNKNOWN,
        )

    @staticmethod
    def _parse_timestamp(
        value: Any,
    ) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _get_salary(
        raw_job: dict[str, Any],
    ) -> str | None:
        compensation = raw_job.get("compensation")

        if not isinstance(compensation, dict):
            return None

        summary = compensation.get("scrapeableCompensationSalarySummary")

        if isinstance(summary, str) and summary.strip():
            return summary.strip()

        return None
