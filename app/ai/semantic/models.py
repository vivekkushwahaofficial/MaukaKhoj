from __future__ import annotations

from pydantic import BaseModel, Field


class SemanticJobAnalysis(BaseModel):
    """AI-derived semantic evidence extracted from one job description."""

    job_id: str = Field(min_length=1)
    role_family: str | None = Field(default=None, min_length=1)
    seniority: str | None = Field(default=None, min_length=1)
    semantic_skills: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    experience_summary: str | None = Field(default=None, min_length=1)
    education_summary: str | None = Field(default=None, min_length=1)
    responsibilities: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SemanticJobAnalysisRequest(BaseModel):
    """Input for semantic analysis of jobs."""

    jobs: tuple[dict, ...] = ()


class SemanticJobAnalysisResponse(BaseModel):
    """Validated semantic analysis for the provided jobs."""

    analyses: tuple[SemanticJobAnalysis, ...] = ()
