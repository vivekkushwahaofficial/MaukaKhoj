from datetime import datetime, timezone

from app.delivery.digest_renderer import DigestRenderer
from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.explanation.models import (
    ExplanationDimension,
    JobExplanation,
)
from app.matching.models import (
    MatchDimension,
    MatchResult,
)
from app.pipeline.models import (
    PipelineResult,
    ProcessedJob,
)
from app.scoring.models import (
    JobScore,
    ScoreDimension,
)


def make_job() -> Job:
    return Job(
        job_id="lever:drivetrain:123",
        source="lever",
        source_job_id="123",
        company="Drivetrain",
        title="Backend Engineer",
        description="Build backend services.",
        location="India",
        remote_type=RemoteType.INDIA_REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY_LEVEL,
        skills=["Java", "Spring Boot"],
        posted_at=datetime(
            2026,
            9,
            14,
            10,
            30,
            tzinfo=timezone.utc,
        ),
        application_url="https://example.com/apply",
    )


def make_processed_job() -> ProcessedJob:
    match_result = MatchResult(
        role=MatchDimension(
            matched=True,
            matched_values=("Backend Developer",),
            evidence=("Target title matches job title.",),
        ),
        skills=MatchDimension(
            matched=True,
            matched_values=("Java", "Spring Boot"),
            evidence=("Required skills match profile skills.",),
        ),
        experience=MatchDimension(
            matched=True,
            evidence=("Entry-level role matches candidate experience.",),
        ),
        education=MatchDimension(matched=None),
        location=MatchDimension(
            matched=True,
            evidence=("India matches profile location.",),
        ),
        remote=MatchDimension(
            matched=True,
            evidence=("India remote is preferred.",),
        ),
        employment=MatchDimension(
            matched=True,
            evidence=("Full-time employment is preferred.",),
        ),
        domain=MatchDimension(
            matched=True,
            evidence=("Backend Development matches the job.",),
        ),
    )

    explanation = JobExplanation(
        dimensions=(
            ExplanationDimension(
                dimension="role",
                status="MATCHED",
                reasons=("Target title matches job title.",),
            ),
            ExplanationDimension(
                dimension="skills",
                status="MATCHED",
                reasons=("Java and Spring Boot match.",),
            ),
        ),
        summary=("Strong backend development match.",),
    )

    score = JobScore(
        total=87.50,
        role=ScoreDimension(
            score=25.0,
            max_score=25.0,
        ),
        skills=ScoreDimension(
            score=27.5,
            max_score=30.0,
        ),
        experience=ScoreDimension(
            score=20.0,
            max_score=20.0,
        ),
        location=ScoreDimension(
            score=15.0,
            max_score=15.0,
        ),
        freshness=ScoreDimension(
            score=0.0,
            max_score=5.0,
        ),
        employment=ScoreDimension(
            score=0.0,
            max_score=5.0,
        ),
    )

    return ProcessedJob(
        job=make_job(),
        match_result=match_result,
        job_score=score,
        explanation=explanation,
        rank=1,
    )


def test_render_html_contains_job_information() -> None:
    result = PipelineResult(
        processed_jobs=(make_processed_job(),),
    )

    html = DigestRenderer().render_html(result)

    assert "MaukaKhoj Job Digest" in html
    assert "Backend Engineer" in html
    assert "Drivetrain" in html
    assert "India" in html
    assert "INDIA_REMOTE" in html
    assert "87.50/100" in html
    assert "Apply for this position" in html
    assert "Why it matches" in html
    assert "MATCHED" in html


def test_render_text_contains_job_information() -> None:
    result = PipelineResult(
        processed_jobs=(make_processed_job(),),
    )

    text = DigestRenderer().render_text(result)

    assert "MaukaKhoj Job Digest" in text
    assert "#1 — Backend Engineer" in text
    assert "Company: Drivetrain" in text
    assert "Location: India" in text
    assert "Match Score: 87.50/100" in text
    assert "https://example.com/apply" in text
    assert "Why it matches:" in text


def test_render_empty_result() -> None:
    result = PipelineResult()

    renderer = DigestRenderer()

    html = renderer.render_html(result)
    text = renderer.render_text(result)

    assert "No matching jobs were found." in html
    assert "No matching jobs were found." in text


def test_render_source_failure() -> None:
    from app.pipeline.models import SourceFailure

    result = PipelineResult(
        source_failures=(
            SourceFailure(
                source="lever",
                error="Connection failed",
            ),
        ),
    )

    renderer = DigestRenderer()

    html = renderer.render_html(result)
    text = renderer.render_text(result)

    assert "Source Failures" in html
    assert "lever" in html
    assert "Connection failed" in html

    assert "Source Failures" in text
    assert "lever: Connection failed" in text
