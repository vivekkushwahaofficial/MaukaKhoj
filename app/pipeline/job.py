import logging
import re
from typing import Any

from app.deduplication.base import JobDeduplicator
from app.domain.education import EducationRequirementStatus
from app.domain.job import Job
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

logger = logging.getLogger(__name__)


class JobPipeline:
    """Orchestrate the complete MaukaKhoj job-processing pipeline."""

    # Explicit senior and management title patterns that should not pass
    # the profile relevance gate for entry-level-oriented profiles.
    _SENIORITY_EXCLUDE_PATTERN = re.compile(
        r"\b("
        r"senior|"
        r"sr\.?|"
        r"staff|"
        r"principal|"
        r"distinguished|"
        r"fellow|"
        r"lead|"
        r"tech\s+lead|"
        r"team\s+lead|"
        r"architect|"
        r"manager|"
        r"management|"
        r"director|"
        r"vp|"
        r"vice\s+president|"
        r"head\s+of|"
        r"chief|"
        r"cto"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def _is_senior_or_management_title(
        cls,
        title: str,
    ) -> bool:
        """Return whether a job title is outside the target seniority."""

        return bool(cls._SENIORITY_EXCLUDE_PATTERN.search(title))

    @classmethod
    def _is_profile_relevant(
        cls,
        job: Job,
        match_result,
        profile: Profile,
    ) -> bool:
        """
        Return whether a job is relevant to the configured profile.

        A job must:
        1. not have an explicitly senior or management title,
        2. satisfy configured location/remote preferences when present,
        3. have at least one core profile match,
        4. satisfy an explicit education requirement when one exists.

        Education with UNKNOWN or NOT_REQUIRED status remains neutral.
        """

        # --------------------------------------------------------------
        # Seniority gate
        # --------------------------------------------------------------
        if cls._is_senior_or_management_title(job.title):
            return False

        # --------------------------------------------------------------
        # Core profile relevance
        # --------------------------------------------------------------
        #
        # If target titles are configured, the job title must match one
        # of those target titles.
        #
        # If no target titles are configured, skills or domain can provide
        # the core relevance signal.
        #
        if profile.target_titles:
            if match_result.role.matched is not True:
                return False
        else:
            if not any(
                (
                    match_result.skills.matched is True,
                    match_result.domain.matched is True,
                )
            ):
                return False

        # --------------------------------------------------------------
        # Location / remote gate
        # --------------------------------------------------------------
        #
        # When the profile has location preferences, the job must match
        # either a configured location or a configured remote preference.
        #
        if profile.locations:
            location_matches = match_result.location.matched is True
            remote_matches = match_result.remote.matched is True

            if not location_matches and not remote_matches:
                return False

        # --------------------------------------------------------------
        # Education gate
        # --------------------------------------------------------------
        #
        # UNKNOWN:
        #   The job does not contain enough structured information.
        #
        # NOT_REQUIRED:
        #   The job explicitly says education is not required.
        #
        # REQUIRED:
        #   The profile must satisfy the structured requirement.
        #
        education_status = job.education_requirement.status

        if education_status == EducationRequirementStatus.REQUIRED:
            if match_result.education.matched is not True:
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
        """Initialize the pipeline with its processing components."""

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

        # --------------------------------------------------------------
        # Source fetching
        # --------------------------------------------------------------
        raw_jobs: list[tuple[str, list[dict[str, Any]]]] = []

        source_failures: list[SourceFailure] = []

        for adapter in self._source_adapters:
            try:
                fetched_jobs = adapter.fetch_jobs()

                logger.info(
                    "Source fetched: %s -> %d jobs",
                    adapter.source_id,
                    len(fetched_jobs),
                )

                raw_jobs.append(
                    (
                        adapter.source_id,
                        fetched_jobs,
                    )
                )

            except Exception as exc:
                source_failures.append(
                    SourceFailure(
                        source=adapter.source_name,
                        error=str(exc),
                    )
                )

                logger.warning(
                    "Source failed: %s -> %s",
                    adapter.source_id,
                    exc,
                )

        total_fetched = sum(
            len(source_jobs)
            for _, source_jobs in raw_jobs
        )
        total_fetched = sum(len(source_jobs) for _, source_jobs in raw_jobs)

        logger.info(
            "Pipeline source fetch total: %d jobs",
            total_fetched,
        )

        logger.info(
            "Pipeline source failures: %d",
            len(source_failures),
        )

        # --------------------------------------------------------------
        # Normalization
        # --------------------------------------------------------------
        normalized_jobs: list[Job] = []

        for source_id, source_jobs in raw_jobs:
            normalized_jobs.extend(
                self._normalization_pipeline.normalize(
                    source_id,
                    source_jobs,
                )
            )

        logger.info(
            "Pipeline normalized: %d jobs",
            len(normalized_jobs),
        )

        # --------------------------------------------------------------
        # Validation
        # --------------------------------------------------------------
        validation_results = []
        valid_jobs = []

        for job in normalized_jobs:
            validation_result = self._validator.validate(job)

            validation_results.append(validation_result)

            if validation_result.is_valid:
                valid_jobs.append(job)

        logger.info(
            "Pipeline validation: %d valid / %d normalized",
            len(valid_jobs),
            len(normalized_jobs),
        )

        # --------------------------------------------------------------
        # Deduplication
        # --------------------------------------------------------------
        deduplication_result = self._deduplicator.deduplicate(valid_jobs)

        logger.info(
            "Pipeline deduplication: %d unique / %d valid",
            len(deduplication_result.unique_jobs),
            len(valid_jobs),
        )

        # --------------------------------------------------------------
        # Hard filtering
        # --------------------------------------------------------------
        filter_result = self._hard_filter.filter(list(deduplication_result.unique_jobs))

        logger.info(
            "Pipeline hard filter: %d eligible / %d rejected",
            len(filter_result.eligible_jobs),
            len(filter_result.rejected_jobs),
        )

        # --------------------------------------------------------------
        # Profile matching and scoring
        # --------------------------------------------------------------
        scored_jobs = []
        match_results = {}
        profile_matched_jobs = []

        for job in filter_result.eligible_jobs:
            match_result = self._matcher.match(
                job,
                profile,
            )

            # Apply seniority, core relevance, location/remote,
            # and education eligibility before scoring.
            if not self._is_profile_relevant(
                job,
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

            scored_jobs.append(
                (
                    job,
                    job_score,
                )
            )

            match_results[job.job_id] = match_result

        logger.info(
            "Pipeline profile relevance: %d matched / %d hard-filter eligible",
            len(profile_matched_jobs),
            len(filter_result.eligible_jobs),
        )

        # --------------------------------------------------------------
        # Ranking
        # --------------------------------------------------------------
        ranking_result = self._ranker.rank(
            scored_jobs,
            limit=limit,
        )

        logger.info(
            "Pipeline ranking: %d selected / %d scored",
            len(ranking_result.selected_jobs),
            len(scored_jobs),
        )

        # --------------------------------------------------------------
        # Explanation + final processed jobs
        # --------------------------------------------------------------
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

        logger.info(
            "Pipeline complete: %d final jobs",
            len(processed_jobs),
        )

        # --------------------------------------------------------------
        # Final pipeline result
        # --------------------------------------------------------------
        return PipelineResult(
            processed_jobs=tuple(processed_jobs),
            profile_matched_jobs=tuple(profile_matched_jobs),
            validation_results=tuple(validation_results),
            duplicates=deduplication_result.duplicates,
            rejected_jobs=filter_result.rejected_jobs,
            source_failures=tuple(source_failures),
        )
