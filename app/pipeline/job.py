from typing import Any

from app.deduplication.base import JobDeduplicator
from app.domain.profile import Profile
from app.explanation.base import JobExplainer
from app.filtering.base import JobHardFilter
from app.matching.base import JobProfileMatcher
from app.normalization.pipeline import NormalizationPipeline
from app.pipeline.models import (
    PipelineResult,
    ProcessedJob,
    ProfileMatchedJob,
    SourceFailure,
)
from app.ranking.base import JobRanker
from app.scoring.base import JobScorer
from app.sources.base import JobSourceAdapter
from app.validation.base import JobValidator


class JobPipeline:
    """Orchestrate the complete MaukaKhoj job-processing pipeline."""

    @staticmethod
    def _is_profile_relevant(
        match_result,
        profile: Profile,
    ) -> bool:
        """Return whether a job is relevant to the configured profile.

        A job must satisfy the configured location/remote preference gate when
        those preferences are present. After that gate passes, at least one
        core profile dimension (role, skills, or domain) must match.
        """

        has_core_match = any(
            (
                match_result.role.matched is True,
                match_result.skills.matched is True,
                match_result.domain.matched is True,
            )
        )

        if not has_core_match:
            return False

        if profile.locations:
            location_matches = match_result.location.matched is True
            remote_matches = match_result.remote.matched is True

            if not location_matches and not remote_matches:
                return False

        return True

    def __init__(
        self,
        *,
        source_adapters: list[JobSourceAdapter],
        normalization_pipeline: NormalizationPipeline,
        validator: JobValidator,
        deduplicator: JobDeduplicator,
        hard_filter: JobHardFilter,
        matcher: JobProfileMatcher,
        scorer: JobScorer,
        ranker: JobRanker,
        explainer: JobExplainer,
    ) -> None:
        self._source_adapters = source_adapters
        self._normalization_pipeline = normalization_pipeline
        self._validator = validator
        self._deduplicator = deduplicator
        self._hard_filter = hard_filter
        self._matcher = matcher
        self._scorer = scorer
        self._ranker = ranker
        self._explainer = explainer

    def run(
        self,
        profile: Profile,
        *,
        limit: int | None = None,
    ) -> PipelineResult:
        """Run all configured job sources through the complete pipeline."""

        raw_jobs: list[tuple[str, list[dict[str, Any]]]] = []
        source_failures: list[SourceFailure] = []

        for adapter in self._source_adapters:
            try:
                fetched_jobs = adapter.fetch_jobs()
                raw_jobs.append((adapter.source_id, fetched_jobs))
            except Exception as exc:
                source_failures.append(
                    SourceFailure(
                        source=adapter.source_name,
                        error=str(exc),
                    )
                )

        normalized_jobs = []

        for source_id, source_jobs in raw_jobs:
            normalized_jobs.extend(
                self._normalization_pipeline.normalize(
                    source_id,
                    source_jobs,
                )
            )

        validation_results = []
        valid_jobs = []

        for job in normalized_jobs:
            validation_result = self._validator.validate(job)

            validation_results.append(validation_result)

            if validation_result.is_valid:
                valid_jobs.append(job)

        deduplication_result = self._deduplicator.deduplicate(valid_jobs)

        filter_result = self._hard_filter.filter(list(deduplication_result.unique_jobs))

        scored_jobs = []
        match_results = {}
        profile_matched_jobs = []

        for job in filter_result.eligible_jobs:
            match_result = self._matcher.match(
                job,
                profile,
            )

            if not self._is_profile_relevant(
                match_result,
                profile,
            ):
                continue

            profile_matched_jobs.append(
                ProfileMatchedJob(
                    job=job,
                    match_result=match_result,
                )
            )

            job_score = self._scorer.score(
                job,
                profile,
                match_result,
            )

            scored_jobs.append((job, job_score))
            match_results[job.job_id] = match_result

        ranking_result = self._ranker.rank(
            scored_jobs,
            limit=limit,
        )

        processed_jobs = []

        for ranked_job in ranking_result.selected_jobs:
            match_result = match_results[ranked_job.job.job_id]

            explanation = self._explainer.explain(
                ranked_job.job,
                profile,
                match_result,
                ranked_job.score,
            )

            processed_jobs.append(
                ProcessedJob(
                    job=ranked_job.job,
                    match_result=match_result,
                    job_score=ranked_job.score,
                    explanation=explanation,
                    rank=ranked_job.rank,
                )
            )

        return PipelineResult(
            processed_jobs=tuple(processed_jobs),
            profile_matched_jobs=tuple(profile_matched_jobs),
            validation_results=tuple(validation_results),
            duplicates=deduplication_result.duplicates,
            rejected_jobs=filter_result.rejected_jobs,
            source_failures=tuple(source_failures),
        )
