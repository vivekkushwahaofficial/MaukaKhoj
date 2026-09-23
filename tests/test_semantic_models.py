from pydantic import ValidationError
import pytest

from app.ai.semantic.models import (
    SemanticJobAnalysis,
    SemanticJobAnalysisRequest,
    SemanticJobAnalysisResponse,
)


def test_semantic_job_analysis_defaults_are_valid() -> None:
    result = SemanticJobAnalysis(job_id="job-1")

    assert result.job_id == "job-1"
    assert result.role_family is None
    assert result.semantic_skills == ()
    assert result.confidence == 0.0


def test_semantic_job_analysis_rejects_invalid_confidence() -> None:
    with pytest.raises(ValidationError):
        SemanticJobAnalysis(job_id="job-1", confidence=1.1)


def test_semantic_job_analysis_request_defaults_are_empty() -> None:
    request = SemanticJobAnalysisRequest()

    assert request.jobs == ()


def test_semantic_job_analysis_response_validates_analysis() -> None:
    response = SemanticJobAnalysisResponse(
        analyses=(
            {
                "job_id": "job-1",
                "role_family": "software_engineering",
                "semantic_skills": ("Java", "Spring Boot"),
                "confidence": 0.9,
            },
        )
    )

    assert response.analyses[0].role_family == "software_engineering"
    assert response.analyses[0].confidence == 0.9
