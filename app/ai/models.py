from __future__ import annotations

from pydantic import BaseModel, Field


class AIJobInsight(BaseModel):
    """AI-generated explanation for one already-ranked job."""

    job_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    strengths: tuple[str, ...] = ()
    cautions: tuple[str, ...] = ()


class AIEnhancementRequest(BaseModel):
    """Input sent to the AI enhancer."""

    profile_summary: str = Field(min_length=1)
    jobs: tuple[dict, ...] = ()


class AIEnhancementResponse(BaseModel):
    """Validated AI response for the selected jobs."""

    insights: tuple[AIJobInsight, ...] = ()
