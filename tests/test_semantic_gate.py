from app.ai.semantic.models import SemanticJobAnalysis
from app.matching.models import MatchDimension, MatchResult
from app.matching.semantic_gate import SemanticRelevanceGate


def make_match_result(role_matched: bool) -> MatchResult:
    role = MatchDimension(matched=role_matched)
    unknown = MatchDimension(matched=None)

    return MatchResult(
        role=role,
        skills=unknown,
        experience=unknown,
        education=unknown,
        location=unknown,
        remote=unknown,
        employment=unknown,
        domain=unknown,
    )


def make_profile():
    from tests.test_job_pipeline import make_profile

    return make_profile()


def make_job(title: str):
    from tests.test_job_pipeline import make_job

    return make_job("job-1", title=title)


def test_deterministic_role_match_passes_without_semantic_analysis() -> None:
    gate = SemanticRelevanceGate()

    assert gate.allows_core_profile(
        job=make_job("Software Engineer"),
        match_result=make_match_result(True),
        profile=make_profile(),
    )


def test_semantic_role_family_can_rescue_title_mismatch() -> None:
    gate = SemanticRelevanceGate()

    analysis = SemanticJobAnalysis(
        job_id="job-1",
        role_family="software_engineering",
        seniority="entry_level",
        confidence=0.9,
    )

    assert gate.allows_core_profile(
        job=make_job("Developer, Agency Success"),
        match_result=make_match_result(False),
        profile=make_profile(),
        semantic_analysis=analysis,
    )


def test_semantic_senior_role_cannot_rescue_title_mismatch() -> None:
    gate = SemanticRelevanceGate()

    analysis = SemanticJobAnalysis(
        job_id="job-1",
        role_family="software_engineering",
        seniority="senior",
        confidence=0.95,
    )

    assert not gate.allows_core_profile(
        job=make_job("Developer, Agency Success"),
        match_result=make_match_result(False),
        profile=make_profile(),
        semantic_analysis=analysis,
    )


def test_explicit_senior_title_always_rejected() -> None:
    gate = SemanticRelevanceGate()

    analysis = SemanticJobAnalysis(
        job_id="job-1",
        role_family="software_engineering",
        seniority="entry_level",
        confidence=0.99,
    )

    assert not gate.allows_core_profile(
        job=make_job("Senior Developer, Agency Success"),
        match_result=make_match_result(False),
        profile=make_profile(),
        semantic_analysis=analysis,
    )


def test_unknown_semantic_role_does_not_rescue_title_mismatch() -> None:
    gate = SemanticRelevanceGate()

    analysis = SemanticJobAnalysis(
        job_id="job-1",
        seniority="entry_level",
        confidence=0.4,
    )

    assert not gate.allows_core_profile(
        job=make_job("Developer, Agency Success"),
        match_result=make_match_result(False),
        profile=make_profile(),
        semantic_analysis=analysis,
    )
