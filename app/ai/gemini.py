from __future__ import annotations

import os
from typing import Any

from google import genai
from google.genai import types

from app.ai.base import JobAIEnhancer
from app.ai.models import (
    AIEnhancementRequest,
    AIEnhancementResponse,
)


class GeminiJobAIEnhancer(JobAIEnhancer):
    """Enhance deterministic job results using one Gemini API call."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-2.5-flash",
    ) -> None:
        if not api_key.strip():
            raise ValueError("Gemini API key must not be empty.")

        if not model.strip():
            raise ValueError("Gemini model must not be empty.")

        self._client = genai.Client(api_key=api_key)
        self._model = model

    @classmethod
    def from_environment(cls) -> "GeminiJobAIEnhancer":
        """Create the Gemini enhancer from environment configuration."""
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required.")

        model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

        return cls(
            api_key=api_key,
            model=model,
        )

    def enhance(
        self,
        request: AIEnhancementRequest,
    ) -> AIEnhancementResponse:
        """Generate insights for all selected jobs in one API call."""

        prompt = self._build_prompt(request)

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AIEnhancementResponse,
                temperature=0.2,
            ),
        )

        parsed = response.parsed

        if isinstance(parsed, AIEnhancementResponse):
            return parsed

        if isinstance(parsed, dict):
            return AIEnhancementResponse.model_validate(parsed)

        raise ValueError("Gemini returned an unexpected structured response.")

    @staticmethod
    def _build_prompt(
        request: AIEnhancementRequest,
    ) -> str:
        """Build a grounded prompt using only deterministic job evidence."""

        return f"""
You are the AI explanation layer of MaukaKhoj, a job discovery
intelligence system.

Your job is NOT to rank jobs, filter jobs, change scores, or decide
whether a job is eligible.

The deterministic MaukaKhoj pipeline has already:
- normalized the jobs
- validated the jobs
- removed duplicates
- applied hard filters
- matched jobs against the profile
- calculated deterministic scores
- ranked the jobs

You must ONLY improve the human-readable explanation.

STRICT RULES:
1. Use only the information provided in the input.
2. Never invent skills, requirements, salary, location, company facts,
   eligibility, benefits, technology, or experience requirements.
3. Never change the deterministic score.
4. Never change the ranking.
5. Never claim that a job is definitely suitable if the evidence is
   incomplete.
6. Treat UNKNOWN information as unknown.
7. Keep each summary concise and useful.
8. Strengths must come from actual matched evidence.
9. Cautions must come from actual missing, unmatched, or unknown evidence.
10. Return one insight for each provided job whenever possible.
11. Use the exact job_id supplied in the input.

PROFILE:
{request.profile_summary}

RANKED JOB DATA:
{request.jobs}

Return structured JSON matching the requested response schema.
""".strip()
