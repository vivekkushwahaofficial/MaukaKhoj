"""Formatting helpers for JobHunt benchmark results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkSummary:
    scanned: int
    eligible: int
    seniority_leaks: int
    location_leaks: int
    stale_leaks: int


def format_summary(summary: BenchmarkSummary) -> str:
    return "\n".join(
        [
            "",
            "=== JobHunt Benchmark ===",
            f"scanned:          {summary.scanned}",
            f"eligible:         {summary.eligible}",
            f"seniority leaks:  {summary.seniority_leaks}",
            f"location leaks:   {summary.location_leaks}",
            f"stale leaks:      {summary.stale_leaks}",
        ]
    )
