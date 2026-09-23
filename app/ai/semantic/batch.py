from __future__ import annotations

import logging

from app.ai.semantic.base import SemanticJobAnalyzer
from app.ai.semantic.models import (
    SemanticJobAnalysis,
    SemanticJobAnalysisRequest,
)

logger = logging.getLogger(__name__)


class SemanticJobBatchAnalyzer:
    """Run semantic analysis over jobs in bounded batches."""

    def __init__(
        self,
        analyzer: SemanticJobAnalyzer,
        *,
        batch_size: int = 8,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        self._analyzer = analyzer
        self._batch_size = batch_size

    def analyze(
        self,
        jobs: tuple[dict, ...],
    ) -> tuple[SemanticJobAnalysis, ...]:
        """Analyze jobs in batches and isolate failures per batch."""

        if not jobs:
            return ()

        analyses_by_job_id: dict[str, SemanticJobAnalysis] = {}

        for start in range(0, len(jobs), self._batch_size):
            batch = jobs[start : start + self._batch_size]

            try:
                response = self._analyzer.analyze(
                    SemanticJobAnalysisRequest(
                        jobs=tuple(batch),
                    )
                )
            except Exception:
                logger.exception(
                    "Semantic analysis batch failed: start=%d size=%d",
                    start,
                    len(batch),
                )
                continue

            for analysis in response.analyses:
                if analysis.job_id not in analyses_by_job_id:
                    analyses_by_job_id[analysis.job_id] = analysis

        return tuple(
            analyses_by_job_id[job["job_id"]]
            for job in jobs
            if isinstance(job.get("job_id"), str)
            and job["job_id"] in analyses_by_job_id
        )
