from unittest.mock import MagicMock, patch

from app.ai.semantic.gemini import GeminiSemanticJobAnalyzer
from app.ai.semantic.models import (
    SemanticJobAnalysisRequest,
    SemanticJobAnalysisResponse,
)


def test_gemini_returns_structured_semantic_response() -> None:
    response = SemanticJobAnalysisResponse(
        analyses=(
            {
                "job_id": "job-1",
                "role_family": "software_engineering",
                "seniority": "entry_level",
                "semantic_skills": ("Java", "Spring Boot", "PostgreSQL"),
                "domains": ("backend_engineering",),
                "experience_summary": "Entry-level backend development experience.",
                "education_summary": "Computer science degree preferred.",
                "responsibilities": ("Build REST APIs.",),
                "evidence": (
                    "Develop backend services using Java and Spring Boot.",
                ),
                "confidence": 0.92,
            },
        )
    )

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value.parsed = response

    with patch(
        "app.ai.semantic.gemini.genai.Client",
        return_value=fake_client,
    ):
        analyzer = GeminiSemanticJobAnalyzer(
            api_key="test-key",
            model="gemini-test",
        )

    request = SemanticJobAnalysisRequest(
        jobs=(
            {
                "job_id": "job-1",
                "title": "Java Backend Developer",
                "description": (
                    "Build REST APIs and backend services using Java, "
                    "Spring Boot, and PostgreSQL."
                ),
            },
        )
    )

    result = analyzer.analyze(request)

    assert result.analyses[0].job_id == "job-1"
    assert result.analyses[0].role_family == "software_engineering"
    assert result.analyses[0].semantic_skills == (
        "Java",
        "Spring Boot",
        "PostgreSQL",
    )

    fake_client.models.generate_content.assert_called_once()


def test_gemini_build_prompt_disallows_scoring_and_ranking() -> None:
    request = SemanticJobAnalysisRequest(
        jobs=(
            {
                "job_id": "job-1",
                "title": "Developer, Agency Success",
                "description": "Build scalable APIs and frontend/backend systems.",
            },
        )
    )

    prompt = GeminiSemanticJobAnalyzer._build_prompt(request)

    assert "do not rank jobs, score jobs, filter jobs" in prompt.lower()
    assert "Do not assign a numeric suitability score." in prompt
    assert "Developer, Agency Success" in prompt
