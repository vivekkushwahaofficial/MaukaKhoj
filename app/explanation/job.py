from app.domain.job import Job
from app.domain.profile import Profile
from app.explanation.base import JobExplainer
from app.explanation.models import ExplanationDimension, JobExplanation
from app.matching.models import MatchDimension, MatchResult
from app.scoring.models import JobScore, ScoreDimension


class DeterministicJobExplainer(JobExplainer):
    """Generate human-readable explanations from existing match and score evidence."""

    def explain(
        self,
        job: Job,
        profile: Profile,
        match_result: MatchResult,
        job_score: JobScore,
    ) -> JobExplanation:
        del profile

        dimensions = (
            self._explain_dimension("role", match_result.role),
            self._explain_dimension("skills", match_result.skills),
            self._explain_dimension("experience", match_result.experience),
            self._explain_dimension("education", match_result.education),
            self._explain_dimension("location", match_result.location),
            self._explain_dimension("remote", match_result.remote),
            self._explain_dimension("employment", match_result.employment),
            self._explain_dimension("domain", match_result.domain),
        )

        summary = self._build_summary(job, job_score)

        return JobExplanation(
            dimensions=dimensions,
            summary=summary,
        )

    @staticmethod
    def _explain_dimension(
        dimension: str,
        match_dimension: MatchDimension,
    ) -> ExplanationDimension:
        status = DeterministicJobExplainer._status(match_dimension.matched)

        reasons = list(match_dimension.evidence)

        if match_dimension.matched_values:
            reasons.append("Matched: " + ", ".join(match_dimension.matched_values))

        if match_dimension.missing_values:
            reasons.append("Missing: " + ", ".join(match_dimension.missing_values))

        return ExplanationDimension(
            dimension=dimension,
            status=status,
            reasons=tuple(reasons),
        )

    @staticmethod
    def _status(matched: bool | None) -> str:
        if matched is True:
            return "MATCHED"

        if matched is False:
            return "NOT_MATCHED"

        return "UNKNOWN"

    @staticmethod
    def _build_summary(
        job: Job,
        job_score: JobScore,
    ) -> tuple[str, ...]:
        summary: list[str] = [
            f"{job.title} at {job.company} scored {job_score.total:.2f}/100."
        ]

        scored_dimensions = (
            ("role", job_score.role),
            ("skills", job_score.skills),
            ("experience", job_score.experience),
            ("location", job_score.location),
            ("freshness", job_score.freshness),
            ("employment", job_score.employment),
        )

        for name, dimension in scored_dimensions:
            if dimension.max_score <= 0:
                continue

            summary.append(
                f"{name.capitalize()} contributed "
                f"{dimension.score:.2f}/{dimension.max_score:.2f}."
            )

        return tuple(summary)
