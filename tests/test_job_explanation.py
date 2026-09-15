from datetime import datetime, timezone

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.explanation.job import DeterministicJobExplainer
from app.explanation.models import ExplanationDimension, JobExplanation
from app.matching.models import MatchDimension, MatchResult
from app.scoring.models import JobScore, ScoreDimension


def make_job() -> Job:
    return Job(
        job_id="job-1",
        source="test",
        source_job_id="job-1",
        company="Example Corp",
        title="Backend Engineer",
        description="Build backend systems.",
        location="India",
        remote_type=RemoteType.INDIA_REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY_LEVEL,
        application_url="https://example.com/jobs/job-1",
        posted_at=datetime(2026, 9, 14, tzinfo=timezone.utc),
    )


def make_match_dimension(
    matched: bool | None,
    *,
    matched_values: tuple[str, ...] = (),
    missing_values: tuple[str, ...] = (),
    evidence: tuple[str, ...] = (),
) -> MatchDimension:
    return MatchDimension(
        matched=matched,
        matched_values=matched_values,
        missing_values=missing_values,
        evidence=evidence,
    )


def make_match_result() -> MatchResult:
    return MatchResult(
        role=make_match_dimension(
            True,
            evidence=("Target title matches.",),
        ),
        skills=make_match_dimension(
            True,
            matched_values=("Java", "Spring Boot"),
            missing_values=("React",),
            evidence=("Relevant backend skills found.",),
        ),
        experience=make_match_dimension(
            True,
            evidence=("Entry-level experience is compatible.",),
        ),
        education=make_match_dimension(
            None,
            evidence=("Job education requirement is unknown.",),
        ),
        location=make_match_dimension(
            True,
            evidence=("India is a preferred location.",),
        ),
        remote=make_match_dimension(
            True,
            evidence=("India remote is preferred.",),
        ),
        employment=make_match_dimension(
            True,
            evidence=("Full-time employment is preferred.",),
        ),
        domain=make_match_dimension(
            False,
            evidence=("No matching domain evidence found.",),
        ),
    )


def make_score_dimension(
    score: float,
    max_score: float,
    evidence: tuple[str, ...] = (),
) -> ScoreDimension:
    return ScoreDimension(
        score=score,
        max_score=max_score,
        evidence=evidence,
    )


def make_job_score() -> JobScore:
    return JobScore(
        total=82.5,
        role=make_score_dimension(25.0, 25.0),
        skills=make_score_dimension(
            22.5,
            30.0,
            evidence=("Matched 3 of 4 relevant skills.",),
        ),
        experience=make_score_dimension(20.0, 20.0),
        location=make_score_dimension(15.0, 15.0),
        freshness=make_score_dimension(0.0, 5.0),
        employment=make_score_dimension(0.0, 5.0),
    )


def test_explain_returns_all_matching_dimensions() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    assert isinstance(result, JobExplanation)

    assert [dimension.dimension for dimension in result.dimensions] == [
        "role",
        "skills",
        "experience",
        "education",
        "location",
        "remote",
        "employment",
        "domain",
    ]


def test_explain_converts_match_statuses() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    statuses = {
        dimension.dimension: dimension.status for dimension in result.dimensions
    }

    assert statuses["role"] == "MATCHED"
    assert statuses["skills"] == "MATCHED"
    assert statuses["education"] == "UNKNOWN"
    assert statuses["domain"] == "NOT_MATCHED"


def test_explain_preserves_match_evidence() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    skills = next(
        dimension for dimension in result.dimensions if dimension.dimension == "skills"
    )

    assert "Relevant backend skills found." in skills.reasons


def test_explain_includes_matched_values() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    skills = next(
        dimension for dimension in result.dimensions if dimension.dimension == "skills"
    )

    assert "Matched: Java, Spring Boot" in skills.reasons


def test_explain_includes_missing_values() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    skills = next(
        dimension for dimension in result.dimensions if dimension.dimension == "skills"
    )

    assert "Missing: React" in skills.reasons


def test_explain_builds_score_summary() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    assert result.summary[0] == ("Backend Engineer at Example Corp scored 82.50/100.")

    assert "Role contributed 25.00/25.00." in result.summary
    assert "Skills contributed 22.50/30.00." in result.summary
    assert "Experience contributed 20.00/20.00." in result.summary
    assert "Location contributed 15.00/15.00." in result.summary


def test_explain_includes_all_scoring_dimensions_in_summary() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    assert any("Role contributed" in item for item in result.summary)
    assert any("Skills contributed" in item for item in result.summary)
    assert any("Experience contributed" in item for item in result.summary)
    assert any("Location contributed" in item for item in result.summary)
    assert any("Freshness contributed" in item for item in result.summary)
    assert any("Employment contributed" in item for item in result.summary)


def test_explain_is_deterministic() -> None:
    explainer = DeterministicJobExplainer()

    first = explainer.explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    second = explainer.explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    assert first == second


def test_explain_does_not_mutate_match_result() -> None:
    match_result = make_match_result()
    original = match_result

    DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=match_result,
        job_score=make_job_score(),
    )

    assert match_result == original


def test_explanation_dimension_is_immutable() -> None:
    dimension = ExplanationDimension(
        dimension="skills",
        status="MATCHED",
        reasons=("Java matched.",),
    )

    try:
        dimension.status = "UNKNOWN"  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("ExplanationDimension should be immutable.")


def test_explanation_has_no_duplicate_dimension_names() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    names = [dimension.dimension for dimension in result.dimensions]

    assert len(names) == len(set(names))


from datetime import datetime, timezone

from app.domain.job import (
    EmploymentType,
    ExperienceLevel,
    Job,
    RemoteType,
)
from app.explanation.job import DeterministicJobExplainer
from app.explanation.models import ExplanationDimension, JobExplanation
from app.matching.models import MatchDimension, MatchResult
from app.scoring.models import JobScore, ScoreDimension


def make_job() -> Job:
    return Job(
        job_id="job-1",
        source="test",
        source_job_id="job-1",
        company="Example Corp",
        title="Backend Engineer",
        description="Build backend systems.",
        location="India",
        remote_type=RemoteType.INDIA_REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY_LEVEL,
        application_url="https://example.com/jobs/job-1",
        posted_at=datetime(2026, 9, 14, tzinfo=timezone.utc),
    )


def make_match_dimension(
    matched: bool | None,
    *,
    matched_values: tuple[str, ...] = (),
    missing_values: tuple[str, ...] = (),
    evidence: tuple[str, ...] = (),
) -> MatchDimension:
    return MatchDimension(
        matched=matched,
        matched_values=matched_values,
        missing_values=missing_values,
        evidence=evidence,
    )


def make_match_result() -> MatchResult:
    return MatchResult(
        role=make_match_dimension(
            True,
            evidence=("Target title matches.",),
        ),
        skills=make_match_dimension(
            True,
            matched_values=("Java", "Spring Boot"),
            missing_values=("React",),
            evidence=("Relevant backend skills found.",),
        ),
        experience=make_match_dimension(
            True,
            evidence=("Entry-level experience is compatible.",),
        ),
        education=make_match_dimension(
            None,
            evidence=("Job education requirement is unknown.",),
        ),
        location=make_match_dimension(
            True,
            evidence=("India is a preferred location.",),
        ),
        remote=make_match_dimension(
            True,
            evidence=("India remote is preferred.",),
        ),
        employment=make_match_dimension(
            True,
            evidence=("Full-time employment is preferred.",),
        ),
        domain=make_match_dimension(
            False,
            evidence=("No matching domain evidence found.",),
        ),
    )


def make_score_dimension(
    score: float,
    max_score: float,
    evidence: tuple[str, ...] = (),
) -> ScoreDimension:
    return ScoreDimension(
        score=score,
        max_score=max_score,
        evidence=evidence,
    )


def make_job_score() -> JobScore:
    return JobScore(
        total=82.5,
        role=make_score_dimension(25.0, 25.0),
        skills=make_score_dimension(
            22.5,
            30.0,
            evidence=("Matched 3 of 4 relevant skills.",),
        ),
        experience=make_score_dimension(20.0, 20.0),
        location=make_score_dimension(15.0, 15.0),
        freshness=make_score_dimension(0.0, 5.0),
        employment=make_score_dimension(0.0, 5.0),
    )


def test_explain_returns_all_matching_dimensions() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    assert isinstance(result, JobExplanation)

    assert [dimension.dimension for dimension in result.dimensions] == [
        "role",
        "skills",
        "experience",
        "education",
        "location",
        "remote",
        "employment",
        "domain",
    ]


def test_explain_converts_match_statuses() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    statuses = {
        dimension.dimension: dimension.status for dimension in result.dimensions
    }

    assert statuses["role"] == "MATCHED"
    assert statuses["skills"] == "MATCHED"
    assert statuses["education"] == "UNKNOWN"
    assert statuses["domain"] == "NOT_MATCHED"


def test_explain_preserves_match_evidence() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    skills = next(
        dimension for dimension in result.dimensions if dimension.dimension == "skills"
    )

    assert "Relevant backend skills found." in skills.reasons


def test_explain_includes_matched_values() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    skills = next(
        dimension for dimension in result.dimensions if dimension.dimension == "skills"
    )

    assert "Matched: Java, Spring Boot" in skills.reasons


def test_explain_includes_missing_values() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    skills = next(
        dimension for dimension in result.dimensions if dimension.dimension == "skills"
    )

    assert "Missing: React" in skills.reasons


def test_explain_builds_score_summary() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    assert result.summary[0] == ("Backend Engineer at Example Corp scored 82.50/100.")

    assert "Role contributed 25.00/25.00." in result.summary
    assert "Skills contributed 22.50/30.00." in result.summary
    assert "Experience contributed 20.00/20.00." in result.summary
    assert "Location contributed 15.00/15.00." in result.summary


def test_explain_includes_all_scoring_dimensions_in_summary() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    assert any("Role contributed" in item for item in result.summary)
    assert any("Skills contributed" in item for item in result.summary)
    assert any("Experience contributed" in item for item in result.summary)
    assert any("Location contributed" in item for item in result.summary)
    assert any("Freshness contributed" in item for item in result.summary)
    assert any("Employment contributed" in item for item in result.summary)


def test_explain_is_deterministic() -> None:
    explainer = DeterministicJobExplainer()

    first = explainer.explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    second = explainer.explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    assert first == second


def test_explain_does_not_mutate_match_result() -> None:
    match_result = make_match_result()
    original = match_result

    DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=match_result,
        job_score=make_job_score(),
    )

    assert match_result == original


def test_explanation_dimension_is_immutable() -> None:
    dimension = ExplanationDimension(
        dimension="skills",
        status="MATCHED",
        reasons=("Java matched.",),
    )

    try:
        dimension.status = "UNKNOWN"  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("ExplanationDimension should be immutable.")


def test_explanation_has_no_duplicate_dimension_names() -> None:
    result = DeterministicJobExplainer().explain(
        make_job(),
        profile=None,  # type: ignore[arg-type]
        match_result=make_match_result(),
        job_score=make_job_score(),
    )

    names = [dimension.dimension for dimension in result.dimensions]

    assert len(names) == len(set(names))
