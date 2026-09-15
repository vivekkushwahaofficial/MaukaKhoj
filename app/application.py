from typing import Any

from app.deduplication.job import CanonicalJobDeduplicator
from app.domain.profile import Profile
from app.explanation.job import DeterministicJobExplainer
from app.filtering.job import CanonicalJobHardFilter
from app.matching.job import CanonicalJobProfileMatcher
from app.normalization.lever import LeverJobNormalizer
from app.normalization.pipeline import NormalizationPipeline
from app.normalization.registry import NormalizationRegistry
from app.pipeline.job import JobPipeline
from app.ranking.job import DeterministicJobRanker
from app.scoring.job import DeterministicJobScorer
from app.sources.http_client import HttpClient
from app.sources.lever import LeverAdapter
from app.sources.registry import SourceRegistry
from app.validation.job import CanonicalJobValidator


class MaukaKhojApplication:
    """Compose and run the configured MaukaKhoj job pipeline."""

    def __init__(
        self,
        *,
        sources_config: dict[str, Any],
        request_timeout_seconds: float = 20.0,
        freshness_config: dict[str, Any] | None = None,
    ) -> None:
        self._http_client = HttpClient(request_timeout_seconds)

        source_registry = SourceRegistry()
        self._register_sources(source_registry)

        source_adapters = []
        normalizer_registry = NormalizationRegistry()

        for source_name, source_config in sources_config.items():
            if source_name == "request_timeout_seconds":
                continue

            adapter, normalizer = source_registry.build(
                source_name,
                source_config,
            )

            source_adapters.append(adapter)
            normalizer_registry.register(
                source_name,
                normalizer,
            )

        self._pipeline = JobPipeline(
            source_adapters=source_adapters,
            normalization_pipeline=NormalizationPipeline(
                normalizer_registry,
            ),
            validator=CanonicalJobValidator(),
            deduplicator=CanonicalJobDeduplicator(),
            hard_filter=CanonicalJobHardFilter(
                freshness_config=freshness_config,
            ),
            matcher=CanonicalJobProfileMatcher(),
            scorer=DeterministicJobScorer(),
            ranker=DeterministicJobRanker(),
            explainer=DeterministicJobExplainer(),
        )

    def _register_sources(
        self,
        registry: SourceRegistry,
    ) -> None:
        """Register all source builders supported by the application."""
        registry.register(
            "lever",
            self._build_lever_source,
        )

    def _build_lever_source(
        self,
        config: dict[str, Any],
    ):
        """Build the Lever adapter and its normalizer."""
        account_name = config.get("account_name")

        if not isinstance(account_name, str) or not account_name.strip():
            raise ValueError("Lever source requires a non-empty 'account_name'.")

        account_name = account_name.strip()

        return (
            LeverAdapter(
                account_name=account_name,
                http_client=self._http_client,
            ),
            LeverJobNormalizer(account_name),
        )

    def run(
        self,
        profile: Profile,
        *,
        limit: int | None = None,
    ):
        """Run the configured job pipeline for a profile."""
        return self._pipeline.run(
            profile,
            limit=limit,
        )

    def close(self) -> None:
        """Release application resources."""
        self._http_client.close()
