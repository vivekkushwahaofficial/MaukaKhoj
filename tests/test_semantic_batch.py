from unittest.mock import MagicMock

from app.ai.semantic.batch import SemanticJobBatchAnalyzer
from app.ai.semantic.models import (
    SemanticJobAnalysis,
    SemanticJobAnalysisRequest,
    SemanticJobAnalysisResponse,
)


def _analysis(job_id: str) -> SemanticJobAnalysis:
    return SemanticJobAnalysis(
        job_id=job_id,
        role_family="software_engineering",
        confidence=0.9,
    )


def test_batch_analyzer_splits_jobs_into_batches() -> None:
    analyzer = MagicMock()

    analyzer.analyze.side_effect = [
        SemanticJobAnalysisResponse(
            analyses=(
                _analysis("job-1"),
                _analysis("job-2"),
            )
        ),
        SemanticJobAnalysisResponse(
            analyses=(
                _analysis("job-3"),
            )
        ),
    ]

    batch_analyzer = SemanticJobBatchAnalyzer(
        analyzer,
        batch_size=2,
    )

    jobs = (
        {"job_id": "job-1"},
        {"job_id": "job-2"},
        {"job_id": "job-3"},
    )

    result = batch_analyzer.analyze(jobs)

    assert [item.job_id for item in result] == [
        "job-1",
        "job-2",
        "job-3",
    ]

    assert analyzer.analyze.call_count == 2

    first_request = analyzer.analyze.call_args_list[0].args[0]
    second_request = analyzer.analyze.call_args_list[1].args[0]

    assert isinstance(first_request, SemanticJobAnalysisRequest)
    assert [job["job_id"] for job in first_request.jobs] == [
        "job-1",
        "job-2",
    ]
    assert [job["job_id"] for job in second_request.jobs] == [
        "job-3",
    ]


def test_batch_analyzer_isolates_failed_batch() -> None:
    analyzer = MagicMock()

    analyzer.analyze.side_effect = [
        RuntimeError("Gemini failure"),
        SemanticJobAnalysisResponse(
            analyses=(
                _analysis("job-3"),
            )
        ),
    ]

    batch_analyzer = SemanticJobBatchAnalyzer(
        analyzer,
        batch_size=2,
    )

    jobs = (
        {"job_id": "job-1"},
        {"job_id": "job-2"},
        {"job_id": "job-3"},
    )

    result = batch_analyzer.analyze(jobs)

    assert [item.job_id for item in result] == ["job-3"]
    assert analyzer.analyze.call_count == 2


def test_batch_analyzer_returns_empty_for_empty_input() -> None:
    analyzer = MagicMock()

    batch_analyzer = SemanticJobBatchAnalyzer(
        analyzer,
        batch_size=2,
    )

    assert batch_analyzer.analyze(()) == ()
    analyzer.analyze.assert_not_called()


def test_batch_analyzer_rejects_invalid_batch_size() -> None:
    analyzer = MagicMock()

    try:
        SemanticJobBatchAnalyzer(
            analyzer,
            batch_size=0,
        )
    except ValueError as exc:
        assert str(exc) == "batch_size must be greater than zero."
    else:
        raise AssertionError("Expected ValueError")
