from abc import ABC, abstractmethod
from typing import Any


class JobSourceAdapter(ABC):
    """Base contract for all MaukaKhoj job source adapters."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the source provider name."""
        raise NotImplementedError

    @property
    def source_id(self) -> str:
        """Return the unique configured source instance identifier."""
        return self.source_name

    @abstractmethod
    def fetch_jobs(self) -> list[dict[str, Any]]:
        """Fetch raw job records from the source."""
        raise NotImplementedError