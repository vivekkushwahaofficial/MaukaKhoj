from __future__ import annotations

import json
import logging

from app.ai.base import JobAIEnhancer
from app.ai.models import AIEnhancementRequest, AIEnhancementResponse
from app.domain.profile import Profile
from app.pipeline.models import PipelineResult

logger = logging.getLogger(__name__)


class DigestService:
    """Coordinate pipeline results, optional AI enhancement, and rendering."""

    def __init__(
        self,
        *,
        application,
        renderer,
        ai_enhancer: JobAIEnhancer | None = None,
    ) -> None:
        self._application = application
        self._renderer = renderer
        self._ai_enhancer = ai_enhancer

    def build_digest(
        self,
        profile: Profile,
        *,
        limit: int | None = None,
    ) -> tuple[str, str]:
        """Build HTML and plain-text digest content."""

        result = self._application.run(
            profile,
            limit=limit,
        )

        ai_response = self._enhance(
            result,
            profile,
        )

        html = self._renderer.render_html(
            result,
            ai_response=ai_response,
        )

        text = self._renderer.render_text(
            result,
            ai_response=ai_response,
        )

        return html, text

    def _enhance(
        self,
        result: PipelineResult,
        profile: Profile,
    ) -> AIEnhancementResponse | None:
        """Enhance ranked jobs using at most one AI request."""

        if self._ai_enhancer is None:
            return None

        if not result.processed_jobs:
            return None

        request = self._build_ai_request(
            result,
            profile,
        )

        try:
            return self._ai_enhancer.enhance(request)
        except Exception:
            logger.exception("AI enhancement failed; using deterministic digest.")
            return None

    @staticmethod
    def _build_ai_request(
        result: PipelineResult,
        profile: Profile,
    ) -> AIEnhancementRequest:
        """Convert deterministic results into grounded AI input."""

        profile_summary = json.dumps(
            {
                "name": profile.name,
                "target_titles": profile.target_titles,
                "skills": profile.skills,
                "experience_years": profile.experience.years,
                "current_title": profile.experience.current_title,
                "locations": profile.locations,
                "remote_preferences": profile.remote_preferences,
                "employment_preferences": profile.employment_preferences,
                "domains": profile.domains,
            },
            ensure_ascii=False,
        )

        jobs: list[dict] = []

        for processed_job in result.processed_jobs:
            job = processed_job.job
            match = processed_job.match_result
            score = processed_job.job_score
            explanation = processed_job.explanation

            jobs.append(
                {
                    "job_id": job.job_id,
                    "rank": processed_job.rank,
                    "company": job.company,
                    "title": job.title,
                    "location": job.location,
                    "remote_type": job.remote_type.value,
                    "employment_type": job.employment_type.value,
                    "experience_level": job.experience_level.value,
                    "skills": job.skills,
                    "score": score.total,
                    "description": job.description[:4000],
                    "match": {
                        "role": {
                            "matched": match.role.matched,
                            "matched_values": match.role.matched_values,
                            "missing_values": match.role.missing_values,
                            "evidence": match.role.evidence,
                        },
                        "skills": {
                            "matched": match.skills.matched,
                            "matched_values": match.skills.matched_values,
                            "missing_values": match.skills.missing_values,
                            "evidence": match.skills.evidence,
                        },
                        "experience": {
                            "matched": match.experience.matched,
                            "matched_values": match.experience.matched_values,
                            "missing_values": match.experience.missing_values,
                            "evidence": match.experience.evidence,
                        },
                        "education": {
                            "matched": match.education.matched,
                            "matched_values": match.education.matched_values,
                            "missing_values": match.education.missing_values,
                            "evidence": match.education.evidence,
                        },
                        "location": {
                            "matched": match.location.matched,
                            "matched_values": match.location.matched_values,
                            "missing_values": match.location.missing_values,
                            "evidence": match.location.evidence,
                        },
                        "remote": {
                            "matched": match.remote.matched,
                            "matched_values": match.remote.matched_values,
                            "missing_values": match.remote.missing_values,
                            "evidence": match.remote.evidence,
                        },
                        "employment": {
                            "matched": match.employment.matched,
                            "matched_values": match.employment.matched_values,
                            "missing_values": match.employment.missing_values,
                            "evidence": match.employment.evidence,
                        },
                        "domain": {
                            "matched": match.domain.matched,
                            "matched_values": match.domain.matched_values,
                            "missing_values": match.domain.missing_values,
                            "evidence": match.domain.evidence,
                        },
                    },
                    "deterministic_explanation": {
                        "summary": explanation.summary,
                        "dimensions": [
                            {
                                "dimension": dimension.dimension,
                                "status": dimension.status,
                                "reasons": dimension.reasons,
                            }
                            for dimension in explanation.dimensions
                        ],
                    },
                }
            )

        return AIEnhancementRequest(
            profile_summary=profile_summary,
            jobs=tuple(jobs),
        )
