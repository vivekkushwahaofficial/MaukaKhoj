from __future__ import annotations

import os

from google import genai
from google.genai import types

from app.ai.semantic.base import SemanticJobAnalyzer
from app.ai.semantic.models import (
    SemanticJobAnalysisRequest,
    SemanticJobAnalysisResponse,
)


class GeminiSemanticJobAnalyzer(SemanticJobAnalyzer):
    """Extract semantic job evidence using one Gemini API call."""

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
    def from_environment(cls) -> "GeminiSemanticJobAnalyzer":
        """Create the semantic analyzer from environment configuration."""
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required.")

        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        return cls(
            api_key=api_key,
            model=model,
        )

    def analyze(
        self,
        request: SemanticJobAnalysisRequest,
    ) -> SemanticJobAnalysisResponse:
        """Analyze all provided jobs in one API call."""
        prompt = self._build_prompt(request)

        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SemanticJobAnalysisResponse,
                temperature=0.1,
            ),
        )

        parsed = response.parsed

        if isinstance(parsed, SemanticJobAnalysisResponse):
            return parsed

        if isinstance(parsed, dict):
            return SemanticJobAnalysisResponse.model_validate(parsed)

        raise ValueError("Gemini returned an unexpected structured response.")

    @staticmethod
    def _build_prompt(
        request: SemanticJobAnalysisRequest,
    ) -> str:
        """Build a grounded prompt using only the supplied job data."""

        return f"""
You are the semantic analysis layer of MaukaKhoj.

Your task is ONLY to extract semantic evidence from the supplied job
postings. You do NOT rank jobs, score jobs, filter jobs, decide eligibility,
or recommend candidates.

For each job, identify:
- role_family: the broad functional family of the role.
- seniority: the seniority explicitly or strongly indicated by the posting.
- semantic_skills: important technical or domain skills described in the job.
- domains: relevant product, engineering, industry, or technical domains.
- experience_summary: concise summary of stated experience expectations.
- education_summary: concise summary of stated education expectations.
- responsibilities: concise key responsibilities.
- evidence: short grounded statements supporting the analysis.
- confidence: confidence from 0.0 to 1.0 in the extracted semantic analysis.

STRICT RULES:
1. Use only information present in the supplied job data.
2. Never invent requirements, skills, technologies, seniority, education,
   responsibilities, domains, salary, location, or company facts.
3. Use null when a field cannot be supported by the supplied information.
4. Do not convert uncertainty into a positive claim.
5. Do not use candidate profile information because none is provided here.
6. Keep evidence concise and grounded in the posting.
7. Preserve the exact job_id supplied for every analysis.
8. Return one analysis for each supplied job whenever possible.
9. Do not assign a numeric suitability score.
10. Do not rank or order jobs by suitability.

JOBS:
{request.jobs}

Return structured JSON matching the requested response schema.
""".strip()
