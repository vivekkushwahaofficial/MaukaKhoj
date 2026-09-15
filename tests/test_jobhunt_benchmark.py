from datetime import datetime, timedelta, timezone

from app.benchmark.jobhunt_rules import evaluate_jobhunt_rules


def test_staff_software_engineer_is_rejected() -> None:
    result = evaluate_jobhunt_rules(
        title="Staff Software Engineer, Platform",
        location="Canada",
        posted_at=datetime.now(timezone.utc),
    )

    assert not result.eligible
    assert not result.title_allowed
    assert not result.location_allowed


def test_india_software_engineer_is_allowed() -> None:
    result = evaluate_jobhunt_rules(
        title="Software Engineer",
        location="Bengaluru, India",
        posted_at=datetime.now(timezone.utc),
    )

    assert result.eligible


def test_remote_software_engineer_is_allowed() -> None:
    result = evaluate_jobhunt_rules(
        title="Software Engineer",
        location="Remote",
        posted_at=datetime.now(timezone.utc),
    )

    assert result.eligible


def test_stale_job_is_rejected() -> None:
    result = evaluate_jobhunt_rules(
        title="Software Engineer",
        location="India",
        posted_at=datetime.now(timezone.utc) - timedelta(days=31),
    )

    assert not result.eligible
    assert not result.freshness_allowed

def test_benchmark_report_detects_seniority_and_location_leaks() -> None:
    from types import SimpleNamespace

    from app.benchmark.evaluator import evaluate_pipeline_result

    job = SimpleNamespace(
        job_id="job-1",
        title="Staff Software Engineer",
        company="Example",
        location="Canada",
        posted_at=datetime.now(timezone.utc),
    )

    processed = SimpleNamespace(job=job)

    validation = SimpleNamespace(is_valid=True)

    result = SimpleNamespace(
        processed_jobs=(processed,),
        validation_results=(validation,),
        duplicates=(),
        rejected_jobs=(),
        source_failures=(),
    )

    report = evaluate_pipeline_result(result)

    assert report.scanned == 1
    assert report.valid == 1
    assert len(report.seniority_leaks) == 1
    assert len(report.location_leaks) == 1
