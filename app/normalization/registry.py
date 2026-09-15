from app.normalization.base import JobNormalizer


class NormalizationRegistry:
    """Registry that maps source instance IDs to job normalizers."""

    def __init__(self) -> None:
        self._normalizers: dict[str, JobNormalizer] = {}

    def register(
        self,
        source_id: str,
        normalizer: JobNormalizer,
    ) -> None:
        """Register a normalizer for a unique source instance."""

        normalized_source_id = source_id.strip().lower()

        if not normalized_source_id:
            raise ValueError("Normalization source ID cannot be empty.")

        if normalized_source_id in self._normalizers:
            raise ValueError(
                f"Normalizer already registered for source ID " f"'{source_id}'."
            )

        self._normalizers[normalized_source_id] = normalizer

    def get(self, source_id: str) -> JobNormalizer:
        """Return the normalizer registered for a source instance."""

        normalized_source_id = source_id.strip().lower()

        if not normalized_source_id:
            raise ValueError("Normalization source ID cannot be empty.")

        try:
            return self._normalizers[normalized_source_id]
        except KeyError as exc:
            raise ValueError(
                f"No job normalizer registered for source ID " f"'{source_id}'."
            ) from exc

    def contains(self, source_id: str) -> bool:
        """Return whether a normalizer is registered for a source instance."""

        normalized_source_id = source_id.strip().lower()

        return normalized_source_id in self._normalizers
