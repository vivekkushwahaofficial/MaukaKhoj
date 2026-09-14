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
from app.validation.job import CanonicalJobValidator


class MaukaKhojApplication:
    """Compose and run the configured MaukaKhoj job pipeline."""

    def __init__(
        self,
        *,
        lever_account_name: str,
        request_timeout_seconds: float = 20.0,
    ) -> None:
        self._http_client = HttpClient(request_timeout_seconds)

        lever_adapter = LeverAdapter(
            account_name=lever_account_name,
            http_client=self._http_client,
        )

        registry = NormalizationRegistry()
        registry.register(
            "lever",
            LeverJobNormalizer(lever_account_name),
        )

        self._pipeline = JobPipeline(
            source_adapters=[lever_adapter],
            normalization_pipeline=NormalizationPipeline(registry),
            validator=CanonicalJobValidator(),
            deduplicator=CanonicalJobDeduplicator(),
            hard_filter=CanonicalJobHardFilter(),
            matcher=CanonicalJobProfileMatcher(),
            scorer=DeterministicJobScorer(),
            ranker=DeterministicJobRanker(),
            explainer=DeterministicJobExplainer(),
        )

    def run(
        self,
        profile: Profile,
        *,
        limit: int | None = None,
    ):
        """Run the configured Lever pipeline for a profile."""
        return self._pipeline.run(
            profile,
            limit=limit,
        )

    def close(self) -> None:
        """Release application resources."""
        self._http_client.close()
