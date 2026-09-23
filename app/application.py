from typing import Any

from app.normalization.skills import SkillExtractor
from app.deduplication.job import CanonicalJobDeduplicator
from app.domain.profile import Profile
from app.explanation.job import DeterministicJobExplainer
from app.filtering.job import CanonicalJobHardFilter
from app.matching.job import CanonicalJobProfileMatcher
from app.normalization.ashby import AshbyJobNormalizer
from app.normalization.base import JobNormalizer
from app.normalization.lever import LeverJobNormalizer
from app.normalization.pipeline import NormalizationPipeline
from app.normalization.registry import NormalizationRegistry
from app.pipeline.job import JobPipeline
from app.ranking.job import DeterministicJobRanker
from app.scoring.job import DeterministicJobScorer
from app.sources.ashby import AshbyAdapter
from app.sources.base import JobSourceAdapter
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
        skill_aliases: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the application from source and pipeline configuration."""
        self._http_client = HttpClient(request_timeout_seconds)

        skill_aliases = skill_aliases or {}
        self._skill_extractor = SkillExtractor(skill_aliases)

        source_registry = SourceRegistry()
        self._register_sources(source_registry)

        source_adapters: list[JobSourceAdapter] = []
        normalizer_registry = NormalizationRegistry()

        for source_name, source_config in sources_config.items():
            if source_name == "request_timeout_seconds":
                continue

            companies = source_config.get("companies")

            if not isinstance(companies, list):
                raise ValueError(f"Source '{source_name}' requires a 'companies' list.")

            for company_config in companies:
                if not isinstance(company_config, dict):
                    raise ValueError(
                        f"Source '{source_name}' companies must be objects."
                    )

                adapter, normalizer = source_registry.build(
                    source_name,
                    company_config,
                )

                source_adapters.append(adapter)

                # Register by unique configured source instance.
                # Example: lever:drivetrain, lever:gohighlevel
                normalizer_registry.register(
                    adapter.source_id,
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
        registry.register("lever", self._build_lever_source)
        registry.register("ashby", self._build_ashby_source)

    def _build_lever_source(
        self,
        config: dict[str, Any],
    ) -> tuple[JobSourceAdapter, JobNormalizer]:
        """Build the Lever adapter and its normalizer."""
        slug = config.get("slug")
        name = config.get("name")

        if not isinstance(slug, str) or not slug.strip():
            raise ValueError("Lever company requires a non-empty 'slug'.")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Lever company requires a non-empty 'name'.")

        slug = slug.strip()
        name = name.strip()

        return (
            LeverAdapter(
                account_name=slug,
                http_client=self._http_client,
            ),
            LeverJobNormalizer(
                slug,
                skill_extractor=self._skill_extractor,
            ),
        )

    def _build_ashby_source(
        self,
        config: dict[str, Any],
    ) -> tuple[JobSourceAdapter, JobNormalizer]:
        """Build the Ashby adapter and its normalizer."""
        slug = config.get("slug")
        name = config.get("name")

        if not isinstance(slug, str) or not slug.strip():
            raise ValueError("Ashby company requires a non-empty 'slug'.")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Ashby company requires a non-empty 'name'.")

        slug = slug.strip()
        name = name.strip()

        return (
            AshbyAdapter(
                job_board_name=slug,
                http_client=self._http_client,
            ),
            AshbyJobNormalizer(
                name,
                skill_extractor=self._skill_extractor,
            ),
        )

    def run(
        self,
        profile: Profile,
        *,
        limit: int | None = None,
    ):
        """Run the configured MaukaKhoj job pipeline."""
        return self._pipeline.run(profile, limit=limit)

    def close(self) -> None:
        """Release application resources."""
        self._http_client.close()
