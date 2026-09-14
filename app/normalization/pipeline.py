from typing import Any

from app.domain.job import Job
from app.normalization.registry import NormalizationRegistry


class NormalizationPipeline:
    """Normalize raw jobs using the normalizer registered for their source."""

    def __init__(self, registry: NormalizationRegistry) -> None:
        self._registry = registry

    def normalize(
        self,
        source: str,
        raw_jobs: list[dict[str, Any]],
    ) -> list[Job]:
        """Normalize all raw jobs from a single source."""

        normalizer = self._registry.get(source)

        return [normalizer.normalize(raw_job) for raw_job in raw_jobs]
