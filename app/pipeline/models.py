from dataclasses import dataclass, field

from app.deduplication.models import DuplicateRecord
from app.domain.job import Job
from app.explanation.models import JobExplanation
from app.filtering.models import RejectedJob
from app.matching.models import MatchResult
from app.scoring.models import JobScore
from app.validation.models import ValidationResult


@dataclass(frozen=True)
class ProcessedJob:
    """Final intelligence result for one eligible canonical job."""

    job: Job
    match_result: MatchResult
    job_score: JobScore
    explanation: JobExplanation
    rank: int


@dataclass(frozen=True)
class ProfileMatchedJob:
    """Canonical job that passed hard filters and profile relevance."""

    job: Job
    match_result: MatchResult


@dataclass(frozen=True)
class SourceFailure:
    """Failure encountered while fetching jobs from one source."""

    source: str
    error: str


@dataclass(frozen=True)
class PipelineResult:
    """Complete result produced by the MaukaKhoj job pipeline."""

    processed_jobs: tuple[ProcessedJob, ...] = field(default_factory=tuple)
    profile_matched_jobs: tuple[ProfileMatchedJob, ...] = field(default_factory=tuple)
    validation_results: tuple[ValidationResult, ...] = field(default_factory=tuple)
    duplicates: tuple[DuplicateRecord, ...] = field(default_factory=tuple)
    rejected_jobs: tuple[RejectedJob, ...] = field(default_factory=tuple)
    source_failures: tuple[SourceFailure, ...] = field(default_factory=tuple)
