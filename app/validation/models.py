from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(str, Enum):
    """Severity of a job validation finding."""

    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation finding."""

    severity: ValidationSeverity
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a canonical job."""

    issues: tuple[ValidationIssue, ...] = field(default_factory=tuple)

    @property
    def is_valid(self) -> bool:
        """Return True when the job has no validation errors."""

        return not any(
            issue.severity == ValidationSeverity.ERROR for issue in self.issues
        )

    @property
    def errors(self) -> tuple[ValidationIssue, ...]:
        """Return all validation errors."""

        return tuple(
            issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR
        )

    @property
    def warnings(self) -> tuple[ValidationIssue, ...]:
        """Return all validation warnings."""

        return tuple(
            issue
            for issue in self.issues
            if issue.severity == ValidationSeverity.WARNING
        )
