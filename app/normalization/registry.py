from app.normalization.base import JobNormalizer


class NormalizationRegistry:
    """Registry that maps source names to job normalizers."""

    def __init__(self) -> None:
        self._normalizers: dict[str, JobNormalizer] = {}

    def register(
        self,
        source: str,
        normalizer: JobNormalizer,
    ) -> None:
        """Register a normalizer for a source."""

        normalized_source = source.strip().lower()

        if not normalized_source:
            raise ValueError("Normalization source cannot be empty.")

        self._normalizers[normalized_source] = normalizer

    def get(self, source: str) -> JobNormalizer:
        """Return the normalizer registered for a source."""

        normalized_source = source.strip().lower()

        if not normalized_source:
            raise ValueError("Normalization source cannot be empty.")

        try:
            return self._normalizers[normalized_source]
        except KeyError as exc:
            raise ValueError(
                f"No job normalizer registered for source '{source}'."
            ) from exc

    def contains(self, source: str) -> bool:
        """Return whether a normalizer is registered for a source."""

        normalized_source = source.strip().lower()

        return normalized_source in self._normalizers