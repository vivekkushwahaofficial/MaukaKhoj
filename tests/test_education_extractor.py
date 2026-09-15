import pytest

from app.domain.education import (
    EducationRequirementStatus,
)
from app.normalization.education import EducationRequirementExtractor


def test_empty_description_returns_unknown():
    result = EducationRequirementExtractor.extract("")

    assert result.status == EducationRequirementStatus.UNKNOWN
    assert result.degree is None
    assert result.field is None
    assert result.minimum_graduation_year is None
    assert result.maximum_graduation_year is None
    assert result.accepts_current_students is None


def test_unrelated_job_description_returns_unknown():
    description = """
    Build backend services using Java and Spring Boot.
    Work with PostgreSQL and Docker in a distributed team.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.UNKNOWN


def test_bachelors_degree_is_detected():
    description = """
    We are looking for a candidate with a Bachelor's degree
    in Computer Science or a related field.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.degree == "Bachelor's degree"
    assert result.field == "Computer Science"


def test_btech_is_detected():
    description = """
    Requirements:
    B.Tech in Computer Science or equivalent experience.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.degree == "B.Tech"
    assert result.field == "Computer Science"


def test_masters_degree_is_detected():
    description = """
    A Master's degree in Computer Science is preferred for this role.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.degree == "Master's degree"
    assert result.field == "Computer Science"


def test_current_students_are_detected():
    description = """
    This opportunity is open to currently enrolled students
    pursuing a bachelor's degree.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.accepts_current_students is True


def test_currently_pursuing_is_detected():
    description = """
    Candidates currently pursuing a B.Tech degree are encouraged to apply.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.accepts_current_students is True


def test_graduation_year_is_detected():
    description = """
    Candidates graduating in 2027 are eligible for this position.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.minimum_graduation_year == 2027
    assert result.maximum_graduation_year == 2027


def test_graduation_range_is_detected():
    description = """
    Students graduating between 2026 and 2027 may apply.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.minimum_graduation_year == 2026
    assert result.maximum_graduation_year == 2027


def test_class_of_year_is_detected():
    description = """
    This internship is intended for students from the class of 2027.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.minimum_graduation_year == 2027
    assert result.maximum_graduation_year == 2027


def test_no_degree_required_is_detected():
    description = """
    No degree required.
    We value practical software development experience.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.NOT_REQUIRED
    assert result.degree is None
    assert result.field is None


@pytest.mark.parametrize(
    ("description", "expected_field"),
    [
        (
            "Bachelor's degree in Information Technology required.",
            "Information Technology",
        ),
        (
            "Degree in Information Systems preferred.",
            "Information Systems",
        ),
        (
            "Bachelor's degree in Software Engineering required.",
            "Software Engineering",
        ),
    ],
)
def test_common_academic_fields_are_detected(
    description: str,
    expected_field: str,
):
    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.field == expected_field


def test_degree_and_student_requirement_can_be_extracted_together():
    description = """
    Currently enrolled students pursuing a B.Tech in Computer Science
    are eligible to apply.
    """

    result = EducationRequirementExtractor.extract(description)

    assert result.status == EducationRequirementStatus.REQUIRED
    assert result.degree == "B.Tech"
    assert result.field == "Computer Science"
    assert result.accepts_current_students is True
