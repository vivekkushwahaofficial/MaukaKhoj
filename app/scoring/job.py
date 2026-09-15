from datetime import datetime, timezone

from app.domain.job import Job
from app.domain.profile import Profile
from app.matching.models import MatchDimension, MatchResult
from app.scoring.models import JobScore, ScoreDimension


class DeterministicJobScorer:
    """Calculate a deterministic 0-100 score from profile-match evidence."""

    def __init__(
        self,
        *,
        role_weight: float = 25.0,
        skills_weight: float = 30.0,
        experience_weight: float = 20.0,
        location_weight: float = 15.0,
        freshness_weight: float = 5.0,
        employment_type_weight: float = 5.0,
    ) -> None:
        """Initialize the scorer with configurable dimension weights."""
        self.role_weight = role_weight
        self.skills_weight = skills_weight
        self.experience_weight = experience_weight
        self.location_weight = location_weight
        self.freshness_weight = freshness_weight
        self.employment_type_weight = employment_type_weight

    def score(
        self,
        job: Job,
        profile: Profile,
        match_result: MatchResult,
        *,
        now: datetime | None = None,
    ) -> JobScore:
        """Return a deterministic score normalized to 0-100.

        Unknown matching evidence does not penalize the job. Only dimensions
        with known evidence contribute to the normalized final score.
        """
        del profile  # Matching evidence already contains profile evaluation.

        role = self._score_dimension(
            match_result.role,
            self.role_weight,
        )
        skills = self._score_skills(
            match_result.skills,
            self.skills_weight,
        )
        experience = self._score_dimension(
            match_result.experience,
            self.experience_weight,
        )
        location = self._score_dimension(
            match_result.location,
            self.location_weight,
        )
        employment = self._score_dimension(
            match_result.employment,
            self.employment_type_weight,
        )
        freshness = self._score_freshness(
            job,
            now=now,
        )

        weighted_dimensions = (
            (role, match_result.role.matched is not None),
            (skills, match_result.skills.matched is not None),
            (experience, match_result.experience.matched is not None),
            (location, match_result.location.matched is not None),
            (freshness, job.posted_at is not None),
            (employment, match_result.employment.matched is not None),
        )

        known_dimensions = tuple(
            dimension for dimension, is_known in weighted_dimensions if is_known
        )

        total_max = sum(dimension.max_score for dimension in known_dimensions)
        total_score = (
            sum(dimension.score for dimension in known_dimensions) / total_max * 100.0
            if total_max > 0
            else 0.0
        )

        total_score = round(total_score, 2)

        return JobScore(
            total=total_score,
            role=role,
            skills=skills,
            experience=experience,
            location=location,
            freshness=freshness,
            employment=employment,
            explanation=self._build_explanation(
                total_score=total_score,
                role=role,
                skills=skills,
                experience=experience,
                location=location,
                freshness=freshness,
                employment=employment,
            ),
        )

    @staticmethod
    def _score_dimension(
        dimension: MatchDimension,
        max_score: float,
    ) -> ScoreDimension:
        """Convert boolean match evidence into a weighted score."""
        if dimension.matched is True:
            score = max_score
        elif dimension.matched is False:
            score = 0.0
        else:
            score = 0.0

        return ScoreDimension(
            score=score,
            max_score=max_score,
            evidence=dimension.evidence,
        )

    @staticmethod
    def _score_skills(
        dimension: MatchDimension,
        max_score: float,
    ) -> ScoreDimension:
        """Calculate a proportional score from matched and missing skills."""
        if dimension.matched is None:
            return ScoreDimension(
                score=0.0,
                max_score=max_score,
                evidence=dimension.evidence,
            )

        matched_count = len(dimension.matched_values)
        missing_count = len(dimension.missing_values)
        total_relevant = matched_count + missing_count

        if total_relevant == 0:
            score = max_score if dimension.matched else 0.0
        else:
            score = max_score * matched_count / total_relevant

        evidence = list(dimension.evidence)

        if total_relevant > 0:
            evidence.append(
                f"Matched {matched_count} of " f"{total_relevant} relevant skills."
            )

        return ScoreDimension(
            score=round(score, 2),
            max_score=max_score,
            evidence=tuple(evidence),
        )

    def _score_freshness(
        self,
        job: Job,
        *,
        now: datetime | None,
    ) -> ScoreDimension:
        """Score freshness from the age of the job posting."""
        if job.posted_at is None:
            return ScoreDimension(
                score=0.0,
                max_score=self.freshness_weight,
                evidence=("Job posting date is unknown.",),
            )

        reference_time = now or datetime.now(timezone.utc)

        posted_at = job.posted_at
        reference_time = self._normalize_datetime(reference_time)
        posted_at = self._normalize_datetime(posted_at)

        age_days = max(
            0.0,
            (reference_time - posted_at).total_seconds() / 86400,
        )

        if age_days <= 1:
            multiplier = 1.0
        elif age_days <= 3:
            multiplier = 0.8
        elif age_days <= 7:
            multiplier = 0.6
        elif age_days <= 14:
            multiplier = 0.4
        elif age_days <= 30:
            multiplier = 0.2
        else:
            multiplier = 0.0

        score = self.freshness_weight * multiplier

        return ScoreDimension(
            score=round(score, 2),
            max_score=self.freshness_weight,
            evidence=(f"Job was posted {age_days:.1f} days ago.",),
        )

    @staticmethod
    def _normalize_datetime(value: datetime) -> datetime:
        """Normalize naive datetimes to UTC for safe comparison."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    @staticmethod
    def _build_explanation(
        *,
        total_score: float,
        role: ScoreDimension,
        skills: ScoreDimension,
        experience: ScoreDimension,
        location: ScoreDimension,
        freshness: ScoreDimension,
        employment: ScoreDimension,
    ) -> tuple[str, ...]:
        """Build deterministic human-readable scoring evidence."""
        dimensions = (
            ("Role", role),
            ("Skills", skills),
            ("Experience", experience),
            ("Location", location),
            ("Freshness", freshness),
            ("Employment", employment),
        )

        explanation = [f"Overall deterministic match score: {total_score:.2f}/100."]

        for name, dimension in dimensions:
            if dimension.score == dimension.max_score:
                explanation.append(f"{name} is a strong match.")
            elif dimension.score == 0:
                explanation.append(f"{name} contributes no score.")
            else:
                explanation.append(
                    f"{name} contributes "
                    f"{dimension.score:.2f}/{dimension.max_score:.2f}."
                )

        return tuple(explanation)
