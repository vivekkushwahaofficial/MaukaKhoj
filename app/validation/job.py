from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.validation.base import JobValidator
from app.validation.models import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)


class CanonicalJobValidator(JobValidator):
    """Validate a canonical Job for pipeline usability."""

    def validate(self, job: Job) -> ValidationResult:
        """Return validation errors and warnings for a canonical Job."""

        issues: list[ValidationIssue] = []

        self._validate_application_url(job, issues)
        self._validate_source_job_id(job, issues)
        self._validate_remote_type(job, issues)
        self._validate_employment_type(job, issues)
        self._validate_experience_level(job, issues)
        self._validate_location(job, issues)
        self._validate_posted_at(job, issues)

        return ValidationResult(issues=tuple(issues))

    @staticmethod
    def _validate_application_url(
        job: Job,
        issues: list[ValidationIssue],
    ) -> None:
        """Ensure the application URL is usable."""

        url = str(job.application_url).strip()

        if not url.startswith(("http://", "https://")):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="INVALID_APPLICATION_URL",
                    message="Application URL must use HTTP or HTTPS.",
                )
            )

    @staticmethod
    def _validate_source_job_id(
        job: Job,
        issues: list[ValidationIssue],
    ) -> None:
        """Warn when the source does not provide an identity."""

        if job.source_job_id is None or not job.source_job_id.strip():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="MISSING_SOURCE_JOB_ID",
                    message="Job does not have a source-specific job ID.",
                )
            )

    @staticmethod
    def _validate_remote_type(
        job: Job,
        issues: list[ValidationIssue],
    ) -> None:
        """Warn when remote classification is unknown."""

        if job.remote_type == RemoteType.UNKNOWN:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="UNKNOWN_REMOTE_TYPE",
                    message="Remote work classification is unknown.",
                )
            )

    @staticmethod
    def _validate_employment_type(
        job: Job,
        issues: list[ValidationIssue],
    ) -> None:
        """Warn when employment type is unknown."""

        if job.employment_type == EmploymentType.UNKNOWN:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="UNKNOWN_EMPLOYMENT_TYPE",
                    message="Employment type is unknown.",
                )
            )

    @staticmethod
    def _validate_experience_level(
        job: Job,
        issues: list[ValidationIssue],
    ) -> None:
        """Warn when experience level is unknown."""

        if job.experience_level == ExperienceLevel.UNKNOWN:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="UNKNOWN_EXPERIENCE_LEVEL",
                    message="Experience level is unknown.",
                )
            )

    @staticmethod
    def _validate_location(
        job: Job,
        issues: list[ValidationIssue],
    ) -> None:
        """Warn when location is unavailable."""

        if job.location is None or not job.location.strip():
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="MISSING_LOCATION",
                    message="Job location is unavailable.",
                )
            )

    @staticmethod
    def _validate_posted_at(
        job: Job,
        issues: list[ValidationIssue],
    ) -> None:
        """Warn when the publication timestamp is unavailable."""

        if job.posted_at is None:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="MISSING_POSTED_AT",
                    message="Job publication timestamp is unavailable.",
                )
            )
