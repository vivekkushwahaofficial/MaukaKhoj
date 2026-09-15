from abc import ABC, abstractmethod
from typing import Any

from app.domain.job import Job


class JobNormalizer(ABC):
    """Base contract for converting raw source jobs into canonical Jobs."""

    @abstractmethod
    def normalize(self, raw_job: dict[str, Any]) -> Job:
        """Convert one raw source job into a canonical Job."""
        raise NotImplementedError
