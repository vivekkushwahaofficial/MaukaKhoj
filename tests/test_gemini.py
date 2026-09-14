from unittest.mock import MagicMock, patch

from app.ai.gemini import GeminiJobAIEnhancer
from app.ai.models import AIEnhancementRequest, AIEnhancementResponse


def test_gemini_returns_structured_response() -> None:
    response = AIEnhancementResponse(
        insights=(
            {
                "job_id": "job-1",
                "summary": "Strong role and skill alignment.",
                "strengths": ("Java", "Spring Boot"),
                "cautions": ("Experience requirement is unknown.",),
            },
        )
    )

    fake_client = MagicMock()
    fake_client.models.generate_content.return_value.parsed = response

    with patch(
        "app.ai.gemini.genai.Client",
        return_value=fake_client,
    ):
        enhancer = GeminiJobAIEnhancer(
            api_key="test-key",
            model="gemini-test",
        )

    request = AIEnhancementRequest(
        profile_summary="Java backend developer seeking entry-level roles.",
        jobs=(
            {
                "job_id": "job-1",
                "title": "Java Developer",
                "company": "Example",
                "score": 90.0,
            },
        ),
    )

    result = enhancer.enhance(request)

    assert result.insights[0].job_id == "job-1"
    assert result.insights[0].summary == "Strong role and skill alignment."

    fake_client.models.generate_content.assert_called_once()
