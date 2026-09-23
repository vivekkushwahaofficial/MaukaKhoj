from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.domain.profile import Profile
from app.matching.base import JobProfileMatcher
from app.matching.models import MatchDimension, MatchResult


class CanonicalJobProfileMatcher(JobProfileMatcher):
    """Deterministically match a canonical job against a user profile."""

    # ------------------------------------------------------------------
    # Degree aliases
    # ------------------------------------------------------------------

    _DEGREE_ALIASES: dict[str, frozenset[str]] = {
        "bachelor": frozenset(
            {
                "bachelor",
                "bachelors",
                "bachelor degree",
                "bachelors degree",
                "bachelor's degree",
                "b.tech",
                "btech",
                "bachelor of technology",
                "b.e.",
                "be",
                "bachelor of engineering",
                "b.sc.",
                "bsc",
                "bachelor of science",
            }
        ),
        "master": frozenset(
            {
                "master",
                "masters",
                "master degree",
                "masters degree",
                "master's degree",
                "m.tech",
                "mtech",
                "master of technology",
                "m.e.",
                "me",
                "master of engineering",
                "m.sc.",
                "msc",
                "master of science",
            }
        ),
    }

    # ------------------------------------------------------------------
    # Academic field aliases
    # ------------------------------------------------------------------

    _FIELD_ALIASES: dict[str, frozenset[str]] = {
        "computer science": frozenset(
            {
                "computer science",
                "computer science engineering",
                "computer engineering",
                "cse",
            }
        ),
        "information technology": frozenset(
            {
                "information technology",
                "information systems",
                "it",
            }
        ),
        "software engineering": frozenset(
            {
                "software engineering",
                "software development",
                "computer science",
                "computer science engineering",
            }
        ),
    }

    def match(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchResult:
        """
        Match every supported dimension independently.

        Each dimension returns True, False, or None:
        - True  -> deterministic match
        - False -> deterministic mismatch
        - None  -> insufficient information / not configured
        """

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
        """
        Match a job title against configured target titles and
        conservative role families.

        Direct target-title matching is checked first.

        Role-family matching exists to recognize equivalent
        software-engineering title variants such as:

        Software Engineer
        Software Developer
        Software Development Engineer

        Seniority is intentionally NOT handled here. The pipeline's
        existing seniority hard-filter remains responsible for rejecting
        senior/staff/lead/manager/director/etc. roles.
        """

        job_title = self._normalize(job.title)

        # --------------------------------------------------------------
        # Direct target-title matching
        # --------------------------------------------------------------
        #
        # Preserve the original behavior first. This means an explicitly
        # configured title remains the strongest deterministic match.
        #
        direct_matches = tuple(
            title
            for title in profile.target_titles
            if self._normalize(title) in job_title
        )

        if direct_matches:
            return MatchDimension(
                matched=True,
                matched_values=direct_matches,
                evidence=("Job title matches a configured target title.",),
            )

        # --------------------------------------------------------------
        # No target titles configured
        # --------------------------------------------------------------

        if not profile.target_titles:
            return MatchDimension(
                matched=None,
                evidence=("No target titles are configured.",),
            )

        normalized_targets = {self._normalize(title) for title in profile.target_titles}

        family_matches_found: list[str] = []

        # --------------------------------------------------------------
        # Software-engineering family
        # --------------------------------------------------------------
        #
        # These title forms are intentionally conservative.
        #
        # Examples that match:
        #   Software Development Engineer
        #   Software Development Engineer II
        #   Software Developer
        #   Software Engineer
        #   Software Engineering Intern
        #   Application Developer
        #
        # Examples that do NOT match:
        #   Business Development Specialist
        #   Graphic Designer
        #   Product Manager
        #   Revenue Operations Analyst
        #
        software_target_configured = any(
            target in normalized_targets
            for target in (
                "software engineer",
                "software developer",
                "software engineering intern",
                "software developer intern",
                "software engineer intern",
            )
        )

        software_title_variants = (
            "software engineer",
            "software engineering",
            "software developer",
            "software development engineer",
            "application engineer",
            "application developer",
        )

        if software_target_configured and any(
            job_title.startswith(variant) for variant in software_title_variants
        ):
            family_matches_found.append(
                "software engineering",
            )

        # --------------------------------------------------------------
        # Backend-engineering family
        # --------------------------------------------------------------

        backend_target_configured = any(
            target in normalized_targets
            for target in (
                "backend engineer",
                "backend developer",
                "backend engineer intern",
                "backend developer intern",
            )
        )

        backend_title_variants = (
            "backend engineer",
            "backend developer",
            "back end engineer",
            "back end developer",
            "backend software engineer",
            "backend software developer",
            "back end software engineer",
            "back end software developer",
        )

        if backend_target_configured and any(
            job_title.startswith(variant) for variant in backend_title_variants
        ):
            family_matches_found.append(
                "backend engineering",
            )

        # --------------------------------------------------------------
        # Java-engineering family
        # --------------------------------------------------------------

        java_target_configured = any(
            target in normalized_targets
            for target in (
                "java developer",
                "java developer intern",
                "java software engineer",
            )
        )

        java_title_variants = (
            "java engineer",
            "java developer",
            "java software engineer",
            "java software developer",
        )

        if java_target_configured and any(
            job_title.startswith(variant) for variant in java_title_variants
        ):
            family_matches_found.append(
                "java engineering",
            )

        # --------------------------------------------------------------
        # Full-stack engineering family
        # --------------------------------------------------------------

        full_stack_target_configured = any(
            target in normalized_targets
            for target in (
                "full stack developer",
                "junior full stack developer",
                "full stack developer intern",
            )
        )

        full_stack_title_variants = (
            "full stack engineer",
            "full stack developer",
            "fullstack engineer",
            "fullstack developer",
        )

        if full_stack_target_configured and any(
            job_title.startswith(variant) for variant in full_stack_title_variants
        ):
            family_matches_found.append(
                "full-stack engineering",
            )

        # --------------------------------------------------------------
        # Family match found
        # --------------------------------------------------------------

        if family_matches_found:
            return MatchDimension(
                matched=True,
                matched_values=tuple(family_matches_found),
                evidence=("Job title matches a configured role family.",),
            )

        # --------------------------------------------------------------
        # No role match
        # --------------------------------------------------------------

        return MatchDimension(
            matched=False,
            missing_values=tuple(profile.target_titles),
            evidence=(
                "Job title does not match configured target titles "
                "or supported role families.",
            ),
        )

    def _match_skills(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        """Match profile skills against the job skills."""

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
                f"{len(matched)} of {len(profile.skills)} " "profile skills matched.",
            ),
        )

    def _match_experience(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        """Match profile experience against the job experience level."""

        if job.experience_level == ExperienceLevel.UNKNOWN:
            return MatchDimension(
                matched=None,
                evidence=("Job experience level is unknown.",),
            )

        if profile.experience.current_title is None and profile.experience.years == 0:
            return MatchDimension(
                matched=None,
                evidence=("No specific profile experience target " "is configured.",),
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
                f"Job experience level is "
                f"{job.experience_level.value}; "
                f"profile experience is {years:.1f} years.",
            ),
        )

    def _match_education(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        """
        Match structured job education requirements against the profile.

        Important behavior:
        - UNKNOWN / NOT_REQUIRED -> None
        - Explicit requirement + no profile education -> False
        - Explicit requirement + matching profile -> True
        - Explicit requirement + mismatch -> False
        """

        requirement = job.education_requirement
        education = profile.education

        if requirement.status.value in {
            "unknown",
            "not_required",
        }:
            return MatchDimension(
                matched=None,
                evidence=(
                    "No explicit education requirement is configured " "for the job.",
                ),
            )

        profile_has_education = any(
            (
                education.degree,
                education.field,
                education.institution,
                education.graduation_year,
                education.is_running,
            )
        )

        if not profile_has_education:
            return MatchDimension(
                matched=False,
                evidence=(
                    "Job has an explicit education requirement, "
                    "but no profile education is configured.",
                ),
            )

        matched_values: list[str] = []
        missing_values: list[str] = []
        evidence: list[str] = []

        # --------------------------------------------------------------
        # Degree requirement
        # --------------------------------------------------------------

        if requirement.degree:
            if not education.degree:
                missing_values.append(requirement.degree)
                evidence.append(
                    f"Required degree is {requirement.degree}, "
                    "but the profile degree is missing.",
                )

            elif not self._degree_matches(
                education.degree,
                requirement.degree,
            ):
                missing_values.append(requirement.degree)
                evidence.append(
                    f"Required degree is {requirement.degree}; "
                    f"profile degree is {education.degree}.",
                )

            else:
                matched_values.append(education.degree)
                evidence.append(
                    f"Profile degree {education.degree} satisfies "
                    f"the required degree {requirement.degree}.",
                )

        # --------------------------------------------------------------
        # Academic field requirement
        # --------------------------------------------------------------

        if requirement.field:
            if not education.field:
                missing_values.append(requirement.field)
                evidence.append(
                    f"Required field is {requirement.field}, "
                    "but the profile field is missing.",
                )

            elif not self._field_matches(
                education.field,
                requirement.field,
            ):
                missing_values.append(requirement.field)
                evidence.append(
                    f"Required field is {requirement.field}; "
                    f"profile field is {education.field}.",
                )

            else:
                matched_values.append(education.field)
                evidence.append(
                    f"Profile field {education.field} satisfies "
                    f"the required field {requirement.field}.",
                )

        # --------------------------------------------------------------
        # Current student requirement
        # --------------------------------------------------------------

        if requirement.accepts_current_students is True:
            if education.is_running:
                matched_values.append(
                    "currently enrolled student",
                )
                evidence.append(
                    "Job accepts currently enrolled students.",
                )
            else:
                missing_values.append(
                    "currently enrolled student",
                )
                evidence.append(
                    "Job accepts currently enrolled students, "
                    "but the profile education is not marked as running.",
                )

        elif requirement.accepts_current_students is False:
            if education.is_running:
                missing_values.append(
                    "currently enrolled student restriction",
                )
                evidence.append(
                    "Job does not accept currently enrolled students.",
                )
            else:
                evidence.append(
                    "Profile education is not currently running.",
                )

        # --------------------------------------------------------------
        # Graduation year requirement
        # --------------------------------------------------------------

        has_graduation_requirement = (
            requirement.minimum_graduation_year is not None
            or requirement.maximum_graduation_year is not None
        )

        if has_graduation_requirement:
            if education.graduation_year is None:
                missing_values.append("graduation year")
                evidence.append(
                    "Job has a graduation-year requirement, "
                    "but profile graduation year is missing.",
                )

            else:
                graduation_year = education.graduation_year

                too_early = (
                    requirement.minimum_graduation_year is not None
                    and graduation_year < requirement.minimum_graduation_year
                )

                too_late = (
                    requirement.maximum_graduation_year is not None
                    and graduation_year > requirement.maximum_graduation_year
                )

                if too_early:
                    missing_values.append(
                        str(
                            requirement.minimum_graduation_year,
                        )
                    )
                    evidence.append(
                        f"Profile graduation year {graduation_year} "
                        f"is earlier than the minimum required year "
                        f"{requirement.minimum_graduation_year}.",
                    )

                elif too_late:
                    missing_values.append(
                        str(
                            requirement.maximum_graduation_year,
                        )
                    )
                    evidence.append(
                        f"Profile graduation year {graduation_year} "
                        f"is later than the maximum allowed year "
                        f"{requirement.maximum_graduation_year}.",
                    )

                else:
                    matched_values.append(
                        str(graduation_year),
                    )
                    evidence.append(
                        f"Profile graduation year {graduation_year} "
                        "satisfies the job requirement.",
                    )

        return MatchDimension(
            matched=not missing_values,
            matched_values=tuple(matched_values),
            missing_values=tuple(missing_values),
            evidence=tuple(evidence),
        )

    def _match_location(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        """Match job location against configured profile locations."""

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
                    "Job location matches a configured " "profile location."
                    if matched
                    else "Job location does not match " "configured profile locations."
                ),
            ),
        )

    def _match_remote(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        """Match job remote type against profile preferences."""

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
            missing_values=tuple(
                preference
                for preference in profile.remote_preferences
                if preference not in matched
            ),
            evidence=(f"Job remote type is {remote_type}.",),
        )

    def _match_employment(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        """Match employment type against profile preferences."""

        if not profile.employment_preferences:
            return MatchDimension(
                matched=None,
                evidence=("No employment preferences are configured.",),
            )

        if job.employment_type == EmploymentType.UNKNOWN:
            return MatchDimension(
                matched=None,
                evidence=("Job employment type is unknown.",),
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
            missing_values=tuple(
                preference
                for preference in profile.employment_preferences
                if preference not in matched
            ),
            evidence=(f"Job employment type is {employment_type}.",),
        )

    def _match_domain(
        self,
        job: Job,
        profile: Profile,
    ) -> MatchDimension:
        """Match configured domains against job information."""

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
                    else "No configured domain was found " "in job information."
                ),
            ),
        )

    def _degree_matches(
        self,
        profile_degree: str,
        required_degree: str,
    ) -> bool:
        """Return True when two degree names belong to the same family."""

        profile = self._normalize(profile_degree)
        required = self._normalize(required_degree)

        if profile == required:
            return True

        return any(
            profile in aliases and required in aliases
            for aliases in self._DEGREE_ALIASES.values()
        )

    def _field_matches(
        self,
        profile_field: str,
        required_field: str,
    ) -> bool:
        """Return True when two academic fields are compatible."""

        profile = self._normalize(profile_field)
        required = self._normalize(required_field)

        if profile == required:
            return True

        return any(
            profile in aliases and required in aliases
            for aliases in self._FIELD_ALIASES.values()
        )

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize text for deterministic case-insensitive matching."""

        return " ".join(value.lower().strip().split())
