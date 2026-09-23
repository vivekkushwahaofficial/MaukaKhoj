from datetime import datetime, timezone
from typing import Any

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.normalization.base import JobNormalizer
from app.normalization.education import EducationRequirementExtractor
from app.normalization.skills import SkillExtractor

class LeverJobNormalizer(JobNormalizer):
    """Normalize a raw Lever posting into a canonical Job."""

    def __init__(
        self,
        account_name: str,
        *,
        skill_extractor: SkillExtractor,
    ) -> None:
        if not account_name.strip():
            raise ValueError("Lever account name cannot be empty.")

        self._account_name = account_name.strip()
        self._skill_extractor = skill_extractor

    def normalize(self, raw_job: dict[str, Any]) -> Job:
        """Convert one raw Lever posting into a canonical Job."""

        # Required Lever fields.
        source_job_id = self._required_string(raw_job, "id")
        title = self._required_string(raw_job, "text")
        description = self._get_description(raw_job)
        apply_url = self._required_string(raw_job, "applyUrl")

        # Lever categories contain location and employment information.
        categories = raw_job.get("categories", {})

        if not isinstance(categories, dict):
            raise ValueError("Lever categories must be an object.")

        location = self._optional_string(categories.get("location"))

        commitment = self._optional_string(categories.get("commitment"))

        workplace_type = self._optional_string(raw_job.get("workplaceType"))

        # Extract structured education requirements from the final
        # normalized plain-text description.
        education_requirement = EducationRequirementExtractor.extract(description)
        skills = self._skill_extractor.extract(description)

        return Job(
            job_id=f"lever:{self._account_name}:{source_job_id}",
            source="lever",
            source_job_id=source_job_id,
            company=self._account_name,
            title=title,
            description=description,
            location=location,
            remote_type=self._map_remote_type(
                workplace_type,
                location,
            ),
            employment_type=self._map_employment_type(commitment),
            experience_level=ExperienceLevel.UNKNOWN,
            skills=skills,
            salary=None,
            posted_at=self._parse_timestamp(raw_job.get("createdAt")),
            updated_at=self._parse_timestamp(raw_job.get("updatedAt")),
            application_url=apply_url,
            company_url=None,
            source_url=self._optional_string(raw_job.get("hostedUrl")),
            education_requirement=education_requirement,
        )

    @staticmethod
    def _required_string(
        raw_job: dict[str, Any],
        field: str,
    ) -> str:
        """Return a required non-empty string field."""

        value = raw_job.get(field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Lever field '{field}' is required.")

        return value.strip()

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        """Return a normalized string or None."""

        if isinstance(value, str) and value.strip():
            return value.strip()

        return None

    @staticmethod
    def _map_remote_type(
        workplace_type: str | None,
        location: str | None,
    ) -> RemoteType:
        """Map Lever workplace metadata to the canonical remote enum."""

        if workplace_type == "remote":
            # Lever explicitly reports India remote.
            if location and location.strip().lower() == "india":
                return RemoteType.INDIA_REMOTE

            # Remote, but country/region could not be safely determined.
            return RemoteType.UNKNOWN

        if workplace_type == "hybrid":
            return RemoteType.HYBRID

        if workplace_type == "onsite":
            return RemoteType.ONSITE

        return RemoteType.UNKNOWN

    @staticmethod
    def _map_employment_type(
        commitment: str | None,
    ) -> EmploymentType:
        """Map Lever commitment metadata to the canonical employment enum."""

        if not commitment:
            return EmploymentType.UNKNOWN

        normalized = commitment.lower()

        if "intern" in normalized:
            return EmploymentType.INTERNSHIP

        if "full" in normalized:
            return EmploymentType.FULL_TIME

        if "part" in normalized:
            return EmploymentType.PART_TIME

        if "contract" in normalized:
            return EmploymentType.CONTRACT

        if "temporary" in normalized:
            return EmploymentType.TEMPORARY

        return EmploymentType.UNKNOWN

    @staticmethod
    def _parse_timestamp(
        value: Any,
    ) -> datetime | None:
        """Convert a Lever millisecond timestamp to UTC datetime."""

        if not isinstance(value, (int, float)):
            return None

        return datetime.fromtimestamp(
            value / 1000,
            tz=timezone.utc,
        )

    @staticmethod
    def _get_description(
        raw_job: dict[str, Any],
    ) -> str:
        """
        Return the best available Lever job description.

        Prefer descriptionPlain because it is already suitable for
        deterministic text extraction. Fall back to HTML description.
        """

        plain_description = raw_job.get("descriptionPlain")

        if isinstance(plain_description, str) and plain_description.strip():
            return plain_description.strip()

        description = raw_job.get("description")

        if isinstance(description, str) and description.strip():
            return description.strip()

        raise ValueError(
            "Lever job must contain a non-empty " "descriptionPlain or description."
        )
