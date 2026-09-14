from app.domain.job import ExperienceLevel, Job, RemoteType
from app.domain.profile import Profile
from app.matching.base import JobProfileMatcher
from app.matching.models import MatchDimension, MatchResult


class CanonicalJobProfileMatcher(JobProfileMatcher):
    """Deterministically match a canonical job against a user profile."""

    def match(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchResult:
        return MatchResult(
            role=self._match_role(job, profile),
            skills=self._match_skills(job, profile),
            experience=self._match_experience(job, profile),
            education=self._match_education(job, profile),
            location=self._match_location(job, profile),
            remote=self._match_remote(job, profile),
            employment=self._match_employment(job, profile),
            domain=self._match_domain(job, profile),
        )

    def _match_role(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        job_title = self._normalize(job.title)

        matched = tuple(
            title
            for title in profile.target_titles
            if self._normalize(title) in job_title
        )

        if matched:
            return MatchDimension(
                matched=True,
                matched_values=matched,
                evidence=("Job title matches a target title.",),
            )

        if not profile.target_titles:
            return MatchDimension(
                matched=None,
                evidence=("No target titles are configured.",),
            )

        return MatchDimension(
            matched=False,
            missing_values=tuple(profile.target_titles),
            evidence=("Job title does not match configured target titles.",),
        )

    def _match_skills(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        job_skills = {self._normalize(skill): skill for skill in job.skills}

        matched = tuple(
            skill for skill in profile.skills if self._normalize(skill) in job_skills
        )

        missing = tuple(
            skill
            for skill in profile.skills
            if self._normalize(skill) not in job_skills
        )

        if not profile.skills:
            return MatchDimension(
                matched=None,
                evidence=("No profile skills are configured.",),
            )

        return MatchDimension(
            matched=bool(matched),
            matched_values=matched,
            missing_values=missing,
            evidence=(
                f"{len(matched)} of {len(profile.skills)} profile skills matched.",
            ),
        )

    def _match_experience(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        if job.experience_level == ExperienceLevel.UNKNOWN:
            return MatchDimension(
                matched=None,
                evidence=("Job experience level is unknown.",),
            )

        # No specific experience target is configured.
        if profile.experience.current_title is None and profile.experience.years == 0:
            return MatchDimension(
                matched=None,
                evidence=("No specific profile experience target is configured.",),
            )

        years = profile.experience.years

        if job.experience_level == ExperienceLevel.INTERN:
            compatible = years <= 1.0

        elif job.experience_level == ExperienceLevel.ENTRY_LEVEL:
            compatible = years <= 2.0

        elif job.experience_level == ExperienceLevel.JUNIOR:
            compatible = years <= 3.0

        elif job.experience_level == ExperienceLevel.MID_LEVEL:
            compatible = 2.0 <= years <= 5.0

        elif job.experience_level == ExperienceLevel.SENIOR:
            compatible = years >= 5.0

        elif job.experience_level == ExperienceLevel.LEAD:
            compatible = years >= 7.0

        else:
            return MatchDimension(
                matched=None,
                evidence=(
                    "Job experience level is not supported "
                    "for deterministic matching.",
                ),
            )

        return MatchDimension(
            matched=compatible,
            evidence=(
                f"Job experience level is {job.experience_level.value}; "
                f"profile experience is {years:.1f} years.",
            ),
        )

    def _match_education(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        if not profile.education.degree and not profile.education.field:
            return MatchDimension(
                matched=None,
                evidence=("No education preferences are configured.",),
            )

        return MatchDimension(
            matched=None,
            evidence=(
                "Canonical job model does not contain structured education requirements.",
            ),
        )

    def _match_location(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        if not profile.locations:
            return MatchDimension(
                matched=None,
                evidence=("No location preferences are configured.",),
            )

        if not job.location:
            return MatchDimension(
                matched=None,
                evidence=("Job location is unavailable.",),
            )

        job_location = self._normalize(job.location)

        matched = tuple(
            location
            for location in profile.locations
            if self._normalize(location) in job_location
        )

        return MatchDimension(
            matched=bool(matched),
            matched_values=matched,
            missing_values=tuple(
                location for location in profile.locations if location not in matched
            ),
            evidence=(
                (
                    "Job location matches a configured profile location."
                    if matched
                    else "Job location does not match configured profile locations."
                ),
            ),
        )

    def _match_remote(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        if not profile.remote_preferences:
            return MatchDimension(
                matched=None,
                evidence=("No remote preferences are configured.",),
            )

        if job.remote_type == RemoteType.UNKNOWN:
            return MatchDimension(
                matched=None,
                evidence=("Job remote type is unknown.",),
            )

        remote_type = job.remote_type.value

        matched = tuple(
            preference
            for preference in profile.remote_preferences
            if self._normalize(preference) == self._normalize(remote_type)
        )

        return MatchDimension(
            matched=bool(matched),
            matched_values=matched,
            evidence=(f"Job remote type is {remote_type}.",),
        )

    def _match_employment(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        if not profile.employment_preferences:
            return MatchDimension(
                matched=None,
                evidence=("No employment preferences are configured.",),
            )

        employment_type = job.employment_type.value

        matched = tuple(
            preference
            for preference in profile.employment_preferences
            if self._normalize(preference) == self._normalize(employment_type)
        )

        return MatchDimension(
            matched=bool(matched),
            matched_values=matched,
            evidence=(f"Job employment type is {employment_type}.",),
        )

    def _match_domain(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        if not profile.domains:
            return MatchDimension(
                matched=None,
                evidence=("No domain preferences are configured.",),
            )

        searchable_text = self._normalize(
            f"{job.title} {job.description} {' '.join(job.skills)}"
        )

        matched = tuple(
            domain
            for domain in profile.domains
            if self._normalize(domain) in searchable_text
        )

        return MatchDimension(
            matched=bool(matched),
            matched_values=matched,
            evidence=(
                (
                    "Configured domain appears in job information."
                    if matched
                    else "No configured domain was found in job information."
                ),
            ),
        )

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize text for deterministic case-insensitive matching."""

        return " ".join(value.lower().strip().split())
