"""Compare MaukaKhoj pipeline output against JobHunt reference rules."""

from __future__ import annotations

from dataclasses import dataclass

from app.benchmark.jobhunt_rules import evaluate_jobhunt_rules
from app.pipeline.models import PipelineResult


@dataclass(frozen=True)
class BenchmarkLeak:
    """One job that violates a JobHunt reference rule."""

    job_id: str
    title: str
    company: str
    location: str
    reason: str


@dataclass(frozen=True)
class BenchmarkReport:
    """Summary of MaukaKhoj output against JobHunt reference rules."""

    scanned: int
    valid: int
    duplicates: int
    hard_rejected: int
    profile_relevant: int
    selected: int
    source_failures: int
    seniority_leaks: tuple[BenchmarkLeak, ...]
    location_leaks: tuple[BenchmarkLeak, ...]
    stale_leaks: tuple[BenchmarkLeak, ...]

    @property
    def total_leaks(self) -> int:
        """Return the total number of detected reference-rule leaks."""

        return (
            len(self.seniority_leaks) + len(self.location_leaks) + len(self.stale_leaks)
        )


def _is_seniority_excluded(title: str) -> bool:
    """Return whether the title matches JobHunt seniority exclusions."""

    lowered = title.lower()

    markers = (
        "senior",
        "sr.",
        "staff",
        "principal",
        "distinguished",
        "fellow",
        "lead",
        "architect",
        "manager",
        "director",
        "vice president",
        "vp",
        "head of",
        "chief",
        "cto",
    )

    return any(marker in lowered for marker in markers)


def evaluate_pipeline_result(
    result: PipelineResult,
    *,
    max_age_days: int = 30,
) -> BenchmarkReport:
    """Evaluate all profile-matched jobs against JobHunt reference rules.

    ``profile_matched_jobs`` represents the complete candidate set after
    hard filtering and profile relevance checks.

    ``processed_jobs`` represents only the final ranked and limited digest
    selection, so it must not be used for leakage detection.
    """

    profile_matched_jobs = result.profile_matched_jobs
    selected_jobs = result.processed_jobs

    # PipelineResult does not currently expose raw or normalized counts,
    # so validation results are the closest authoritative count available.
    valid_count = sum(
        1
        for validation_result in result.validation_results
        if validation_result.is_valid
    )

    rejected_count = len(result.rejected_jobs)
    duplicate_count = len(result.duplicates)
    profile_relevant_count = len(profile_matched_jobs)

    seniority_leaks: list[BenchmarkLeak] = []
    location_leaks: list[BenchmarkLeak] = []
    stale_leaks: list[BenchmarkLeak] = []

    for matched_job in profile_matched_jobs:
        job = matched_job.job

        rules = evaluate_jobhunt_rules(
            title=job.title,
            location=job.location or "",
            posted_at=job.posted_at,
            max_age_days=max_age_days,
        )

        base = {
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "location": job.location or "",
        }

        if _is_seniority_excluded(job.title):
            seniority_leaks.append(
                BenchmarkLeak(
                    **base,
                    reason="JobHunt exclude-title rule",
                )
            )

        if not rules.location_allowed:
            location_leaks.append(
                BenchmarkLeak(
                    **base,
                    reason="JobHunt India/remote location rule",
                )
            )

        if not rules.freshness_allowed:
            stale_leaks.append(
                BenchmarkLeak(
                    **base,
                    reason="JobHunt freshness rule",
                )
            )

    return BenchmarkReport(
        scanned=len(result.validation_results),
        valid=valid_count,
        duplicates=duplicate_count,
        hard_rejected=rejected_count,
        profile_relevant=profile_relevant_count,
        selected=len(selected_jobs),
        source_failures=len(result.source_failures),
        seniority_leaks=tuple(seniority_leaks),
        location_leaks=tuple(location_leaks),
        stale_leaks=tuple(stale_leaks),
    )


def format_report(report: BenchmarkReport) -> str:
    """Format a benchmark report for human-readable console output."""

    lines = [
        "",
        "=== MaukaKhoj vs JobHunt Benchmark ===",
        f"jobs validated:       {report.scanned}",
        f"valid jobs:           {report.valid}",
        f"duplicates:           {report.duplicates}",
        f"hard rejected:        {report.hard_rejected}",
        f"profile relevant:     {report.profile_relevant}",
        f"selected:             {report.selected}",
        f"source failures:      {report.source_failures}",
        "",
        "Reference-rule leakage",
        f"seniority leaks:      {len(report.seniority_leaks)}",
        f"location leaks:       {len(report.location_leaks)}",
        f"stale leaks:          {len(report.stale_leaks)}",
        f"total leaks:          {report.total_leaks}",
    ]

    for category, leaks in (
        ("seniority", report.seniority_leaks),
        ("location", report.location_leaks),
        ("stale", report.stale_leaks),
    ):
        if not leaks:
            continue

        lines.extend(["", f"{category.upper()} LEAKS"])

        for leak in leaks:
            lines.append(
                f"- {leak.title} | {leak.company} | " f"{leak.location} | {leak.reason}"
            )

    return "\n".join(lines)
