from abc import ABC, abstractmethod

from app.domain.job import Job
from app.validation.models import ValidationResult


class JobValidator(ABC):
    """Base contract for validating canonical Jobs."""

    @abstractmethod
    def validate(self, job: Job) -> ValidationResult:
        """Validate one canonical Job."""

        raise NotImplementedError
