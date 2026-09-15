from collections.abc import Callable
from typing import Any

from app.normalization.base import JobNormalizer
from app.sources.base import JobSourceAdapter

SourceBuilder = Callable[
    [dict[str, Any]],
    tuple[JobSourceAdapter, JobNormalizer],
]


class SourceRegistry:
    """Registry for configured job source adapters and normalizers."""

    def __init__(self) -> None:
        self._builders: dict[str, SourceBuilder] = {}

    def register(
        self,
        source: str,
        builder: SourceBuilder,
    ) -> None:
        """Register a source builder."""

        normalized_source = source.strip().lower()

        if not normalized_source:
            raise ValueError("Source name cannot be empty.")

        self._builders[normalized_source] = builder

    def build(
        self,
        source: str,
        config: dict[str, Any],
    ) -> tuple[JobSourceAdapter, JobNormalizer]:
        """Build the adapter and normalizer for a configured source."""

        normalized_source = source.strip().lower()

        if not normalized_source:
            raise ValueError("Source name cannot be empty.")

        try:
            builder = self._builders[normalized_source]
        except KeyError as exc:
            raise ValueError(
                f"No source builder registered for source '{source}'."
            ) from exc

        return builder(config)
