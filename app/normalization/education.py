import re

from app.domain.education import (
    EducationRequirement,
    EducationRequirementStatus,
)


class EducationRequirementExtractor:
    """
    Extract structured education requirements from job-description text.

    The extractor is intentionally conservative:
    - REQUIRED: explicit education eligibility is detected.
    - NOT_REQUIRED: the text explicitly says a degree is not required.
    - UNKNOWN: there is not enough evidence to determine an education rule.

    The extractor never invents an education requirement from missing data.
    """

    # ---------------------------------------------------------------
    # Degree patterns
    # ---------------------------------------------------------------
    #
    # These patterns recognize common degree names used in job postings.
    #
    _DEGREE_PATTERNS: tuple[tuple[str, str], ...] = (
        (
            r"\b(?:b\.?\s*tech|btech|" r"bachelor(?:'s)?\s+of\s+technology)\b",
            "B.Tech",
        ),
        (
            r"\b(?:b\.?\s*e\.?|be|" r"bachelor(?:'s)?\s+of\s+engineering)\b",
            "B.E.",
        ),
        (
            r"\b(?:b\.?\s*sc\.?|bsc|" r"bachelor(?:'s)?\s+of\s+science)\b",
            "B.Sc.",
        ),
        (
            r"\b(?:m\.?\s*tech|mtech|" r"master(?:'s)?\s+of\s+technology)\b",
            "M.Tech",
        ),
        (
            r"\b(?:m\.?\s*e\.?|me|" r"master(?:'s)?\s+of\s+engineering)\b",
            "M.E.",
        ),
        (
            r"\b(?:m\.?\s*sc\.?|msc|" r"master(?:'s)?\s+of\s+science)\b",
            "M.Sc.",
        ),
        (
            r"\bbachelor(?:'s)?\s+degree\b",
            "Bachelor's degree",
        ),
        (
            r"\bmaster(?:'s)?\s+degree\b",
            "Master's degree",
        ),
    )

    # ---------------------------------------------------------------
    # Academic-field patterns
    # ---------------------------------------------------------------
    _FIELD_PATTERNS: tuple[tuple[str, str], ...] = (
        (
            r"\bcomputer\s+science\s+engineering\b",
            "Computer Science",
        ),
        (
            r"\bcomputer\s+science\b",
            "Computer Science",
        ),
        (
            r"\bcomputer\s+engineering\b",
            "Computer Engineering",
        ),
        (
            r"\binformation\s+technology\b",
            "Information Technology",
        ),
        (
            r"\binformation\s+systems\b",
            "Information Systems",
        ),
        (
            r"\bsoftware\s+engineering\b",
            "Software Engineering",
        ),
    )

    # ---------------------------------------------------------------
    # Current-student patterns
    # ---------------------------------------------------------------
    _CURRENT_STUDENT_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(
            r"\bcurrently\s+enrolled\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bcurrently\s+pursuing\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bpursuing\s+(?:a|an)?\s*"
            r"(?:bachelor|master|b\.?\s*tech|m\.?\s*tech)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\benrolled\s+in\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bactive\s+student\b",
            re.IGNORECASE,
        ),
    )

    # ---------------------------------------------------------------
    # Explicit statements that students are eligible
    # ---------------------------------------------------------------
    _STUDENT_ACCEPTANCE_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(
            r"\b(?:students?|undergraduates?|graduates?)\s+"
            r"(?:may|can|are\s+encouraged\s+to)\s+apply\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bcurrently\s+enrolled\s+" r"(?:students?|candidates?)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:open|available)\s+to\s+" r"(?:current\s+)?students?\b",
            re.IGNORECASE,
        ),
    )

    # ---------------------------------------------------------------
    # Explicit "no degree required" patterns
    # ---------------------------------------------------------------
    _NOT_REQUIRED_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(
            r"\bno\s+(?:formal\s+)?degree\s+required\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bdegree\s+not\s+required\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bno\s+degree\s+required\b",
            re.IGNORECASE,
        ),
    )

    # ---------------------------------------------------------------
    # Graduation-year patterns
    # ---------------------------------------------------------------
    #
    # Supports:
    #   graduating in 2027
    #   graduation in 2027
    #   graduating between 2026 and 2027
    #   graduating between 2026-2027
    #   graduating between 2026 to 2027
    #   graduating between 2026 through 2027
    #   graduating between 2026 and 2027
    #   class of 2027
    #
    _GRADUATION_RANGE_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(
            r"\b(?:graduating|graduation)\s+"
            r"(?:in\s+|between\s+)"
            r"(?P<start>20\d{2})"
            r"(?:\s*(?:-|to|through|and)\s*"
            r"(?P<end>20\d{2}))?"
            r"\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bclass\s+of\s+"
            r"(?P<start>20\d{2})"
            r"(?:\s*(?:-|to|through|and)\s*"
            r"(?P<end>20\d{2}))?"
            r"\b",
            re.IGNORECASE,
        ),
    )

    @classmethod
    def extract(
        cls,
        description: str,
    ) -> EducationRequirement:
        """
        Extract a structured education requirement from job text.
        """

        text = cls._normalize_text(description)

        # Empty descriptions cannot provide education information.
        if not text:
            return EducationRequirement(
                status=EducationRequirementStatus.UNKNOWN,
            )

        # An explicit "degree not required" statement takes precedence.
        if cls._contains_any(
            text,
            cls._NOT_REQUIRED_PATTERNS,
        ):
            return EducationRequirement(
                status=EducationRequirementStatus.NOT_REQUIRED,
            )

        # Extract degree and field independently.
        degree = cls._extract_degree(text)
        field = cls._extract_field(text)

        # Determine whether current students are explicitly accepted.
        accepts_current_students = cls._extract_student_acceptance(text)

        # Extract graduation-year information.
        minimum_graduation_year: int | None = None
        maximum_graduation_year: int | None = None

        for pattern in cls._GRADUATION_RANGE_PATTERNS:
            match = pattern.search(text)

            if not match:
                continue

            start = match.group("start")
            end = match.group("end")

            minimum_graduation_year = int(start)

            # A single year such as "graduating in 2027" represents
            # the same minimum and maximum year.
            if end is None:
                maximum_graduation_year = minimum_graduation_year
            else:
                maximum_graduation_year = int(end)

            break

        # Any explicit education-related signal means the job has
        # a structured education requirement.
        has_requirement = any(
            (
                degree is not None,
                field is not None,
                accepts_current_students is not None,
                minimum_graduation_year is not None,
                maximum_graduation_year is not None,
            )
        )

        # No evidence means we intentionally preserve UNKNOWN.
        if not has_requirement:
            return EducationRequirement(
                status=EducationRequirementStatus.UNKNOWN,
            )

        return EducationRequirement(
            status=EducationRequirementStatus.REQUIRED,
            degree=degree,
            field=field,
            minimum_graduation_year=minimum_graduation_year,
            maximum_graduation_year=maximum_graduation_year,
            accepts_current_students=accepts_current_students,
        )

    @classmethod
    def _extract_degree(
        cls,
        text: str,
    ) -> str | None:
        """Return the first recognized degree from the job text."""

        for pattern, degree in cls._DEGREE_PATTERNS:
            if re.search(
                pattern,
                text,
                re.IGNORECASE,
            ):
                return degree

        return None

    @classmethod
    def _extract_field(
        cls,
        text: str,
    ) -> str | None:
        """Return the first recognized academic field."""

        for pattern, field in cls._FIELD_PATTERNS:
            if re.search(
                pattern,
                text,
                re.IGNORECASE,
            ):
                return field

        return None

    @classmethod
    def _extract_student_acceptance(
        cls,
        text: str,
    ) -> bool | None:
        """
        Determine whether the posting explicitly allows current students.

        We return None when there is no evidence rather than guessing.
        """

        # Strong explicit acceptance signal.
        if cls._contains_any(
            text,
            cls._STUDENT_ACCEPTANCE_PATTERNS,
        ):
            return True

        # Current-student wording is also treated as positive evidence.
        if cls._contains_any(
            text,
            cls._CURRENT_STUDENT_PATTERNS,
        ):
            return True

        return None

    @staticmethod
    def _contains_any(
        text: str,
        patterns: tuple[re.Pattern[str], ...],
    ) -> bool:
        """Return True if any compiled pattern matches the text."""

        return any(pattern.search(text) is not None for pattern in patterns)

    @staticmethod
    def _normalize_text(value: str) -> str:
        """
        Normalize whitespace while preserving meaningful text.

        Lowercasing makes regex matching case-insensitive and deterministic.
        """

        return " ".join(value.lower().strip().split())
