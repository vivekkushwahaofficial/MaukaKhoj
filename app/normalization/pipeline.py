from typing import Any

from app.domain.job import Job
from app.normalization.registry import NormalizationRegistry


class NormalizationPipeline:
    """Normalize raw jobs using the normalizer for each source instance."""

    def __init__(self, registry: NormalizationRegistry) -> None:
        self._registry = registry

    def normalize(
        self,
        source_id: str,
        raw_jobs: list[dict[str, Any]],
    ) -> list[Job]:
        """Normalize all raw jobs from a single source instance."""

        normalizer = self._registry.get(source_id)

        return [normalizer.normalize(raw_job) for raw_job in raw_jobs]
