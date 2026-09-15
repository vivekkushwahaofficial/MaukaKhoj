from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.ai.models import AIEnhancementResponse, AIJobInsight
from app.delivery.digest_service import DigestService
from app.domain.job import EmploymentType, ExperienceLevel, Job, RemoteType
from app.domain.profile import Education, Experience, Profile
from app.pipeline.models import PipelineResult, ProcessedJob


def make_profile() -> Profile:
    return Profile(
        name="Vivek",
        target_titles=["Backend Engineer"],
        skills=["Java", "Spring Boot"],
        experience=Experience(
            years=0.0,
            current_title="Java Tech Stack Intern",
        ),
        education=Education(
            degree="B.Tech",
            field="Computer Science",
            institution="OIST",
        ),
        locations=["India"],
        remote_preferences=["INDIA_REMOTE"],
        employment_preferences=["FULL_TIME"],
        domains=["Backend Development"],
    )


def make_job() -> Job:
    return Job(
        job_id="lever:drivetrain:123",
        source="lever",
        source_job_id="123",
        company="Drivetrain",
        title="Backend Engineer",
        description="Backend engineering role using Java and Spring Boot.",
        location="India",
        remote_type=RemoteType.INDIA_REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY_LEVEL,
        skills=["Java", "Spring Boot"],
        posted_at=datetime(2026, 9, 14, 10, 30, tzinfo=timezone.utc),
        application_url="https://example.com/apply",
        company_url="https://example.com",
        source_url="https://example.com/job",
    )


def make_processed_job() -> ProcessedJob:
    # Use mocks here because DigestService only needs these objects
    # to serialize their already-computed pipeline information.
    match_result = Mock()
    match_result.role.model_dump.return_value = {"status": "MATCH"}
    match_result.skills.model_dump.return_value = {"status": "MATCH"}
    match_result.experience.model_dump.return_value = {"status": "MATCH"}
    match_result.education.model_dump.return_value = {"status": "UNKNOWN"}
    match_result.location.model_dump.return_value = {"status": "MATCH"}
    match_result.remote.model_dump.return_value = {"status": "MATCH"}
    match_result.employment.model_dump.return_value = {"status": "MATCH"}
    match_result.domain.model_dump.return_value = {"status": "MATCH"}

    job_score = Mock()
    job_score.total = 92.5

    dimension = Mock()
    dimension.dimension = "skills"
    dimension.status = "MATCH"
    dimension.reasons = ("Java matches.", "Spring Boot matches.")

    explanation = Mock()
    explanation.summary = "Strong backend match."
    explanation.dimensions = (dimension,)

    return ProcessedJob(
        job=make_job(),
        match_result=match_result,
        job_score=job_score,
        explanation=explanation,
        rank=1,
    )


def make_ai_response() -> AIEnhancementResponse:
    return AIEnhancementResponse(
        insights=(
            AIJobInsight(
                job_id="lever:drivetrain:123",
                summary="Strong alignment with the backend development profile.",
                strengths=("Java matches.", "Spring Boot matches."),
                cautions=("Education requirements are unknown.",),
            ),
        )
    )


def make_service(
    *,
    application: Mock | None = None,
    renderer: Mock | None = None,
    ai_enhancer: Mock | None = None,
) -> tuple[DigestService, Mock, Mock, Mock]:
    application = application or Mock()
    renderer = renderer or Mock()
    ai_enhancer = ai_enhancer or Mock()

    return (
        DigestService(
            application=application,
            renderer=renderer,
            ai_enhancer=ai_enhancer,
        ),
        application,
        renderer,
        ai_enhancer,
    )


def test_build_digest_runs_application_and_renders_both_formats() -> None:
    processed_job = make_processed_job()

    application = Mock()
    application.run.return_value = PipelineResult(
        processed_jobs=(processed_job,),
    )

    renderer = Mock()
    renderer.render_html.return_value = "<html>digest</html>"
    renderer.render_text.return_value = "digest"

    ai_enhancer = Mock()
    ai_response = make_ai_response()
    ai_enhancer.enhance.return_value = ai_response

    service = DigestService(
        application=application,
        renderer=renderer,
        ai_enhancer=ai_enhancer,
    )

    html, text = service.build_digest(make_profile(), limit=6)

    assert html == "<html>digest</html>"
    assert text == "digest"

    application.run.assert_called_once()
    ai_enhancer.enhance.assert_called_once()

    renderer.render_html.assert_called_once_with(
        application.run.return_value,
        ai_response=ai_response,
    )
    renderer.render_text.assert_called_once_with(
        application.run.return_value,
        ai_response=ai_response,
    )


def test_build_digest_skips_ai_when_no_processed_jobs() -> None:
    application = Mock()
    application.run.return_value = PipelineResult()

    renderer = Mock()
    renderer.render_html.return_value = "<html>digest</html>"
    renderer.render_text.return_value = "digest"

    ai_enhancer = Mock()

    service = DigestService(
        application=application,
        renderer=renderer,
        ai_enhancer=ai_enhancer,
    )

    html, text = service.build_digest(make_profile())

    assert html == "<html>digest</html>"
    assert text == "digest"

    ai_enhancer.enhance.assert_not_called()

    renderer.render_html.assert_called_once_with(
        application.run.return_value,
        ai_response=None,
    )
    renderer.render_text.assert_called_once_with(
        application.run.return_value,
        ai_response=None,
    )


def test_build_digest_skips_ai_when_enhancer_is_not_configured() -> None:
    application = Mock()
    application.run.return_value = PipelineResult(
        processed_jobs=(make_processed_job(),),
    )

    renderer = Mock()
    renderer.render_html.return_value = "<html>digest</html>"
    renderer.render_text.return_value = "digest"

    service = DigestService(
        application=application,
        renderer=renderer,
        ai_enhancer=None,
    )

    html, text = service.build_digest(make_profile())

    assert html == "<html>digest</html>"
    assert text == "digest"

    renderer.render_html.assert_called_once_with(
        application.run.return_value,
        ai_response=None,
    )
    renderer.render_text.assert_called_once_with(
        application.run.return_value,
        ai_response=None,
    )


def test_build_digest_falls_back_to_deterministic_digest_when_ai_fails(
    caplog: pytest.LogCaptureFixture,
) -> None:
    application = Mock()
    application.run.return_value = PipelineResult(
        processed_jobs=(make_processed_job(),),
    )

    renderer = Mock()
    renderer.render_html.return_value = "<html>deterministic</html>"
    renderer.render_text.return_value = "deterministic"

    ai_enhancer = Mock()
    ai_enhancer.enhance.side_effect = RuntimeError("Gemini unavailable")

    service = DigestService(
        application=application,
        renderer=renderer,
        ai_enhancer=ai_enhancer,
    )

    with caplog.at_level("ERROR"):
        html, text = service.build_digest(make_profile())

    assert html == "<html>deterministic</html>"
    assert text == "deterministic"

    renderer.render_html.assert_called_once_with(
        application.run.return_value,
        ai_response=None,
    )
    renderer.render_text.assert_called_once_with(
        application.run.return_value,
        ai_response=None,
    )

    assert "AI enhancement failed" in caplog.text


def test_build_digest_passes_limit_to_application() -> None:
    application = Mock()
    application.run.return_value = PipelineResult()

    renderer = Mock()
    renderer.render_html.return_value = "html"
    renderer.render_text.return_value = "text"

    service = DigestService(
        application=application,
        renderer=renderer,
        ai_enhancer=None,
    )

    service.build_digest(make_profile(), limit=6)

    application.run.assert_called_once_with(
        make_profile(),
        limit=6,
    )
