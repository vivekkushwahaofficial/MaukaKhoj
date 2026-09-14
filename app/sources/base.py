from abc import ABC, abstractmethod
from typing import Any


class JobSourceAdapter(ABC):
    """Base contract for all MaukaKhoj job source adapters."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the unique name of the job source."""
        raise NotImplementedError

    @abstractmethod
    def fetch_jobs(self) -> list[dict[str, Any]]:
        """Fetch raw job records from the source."""
        raise NotImplementedError
