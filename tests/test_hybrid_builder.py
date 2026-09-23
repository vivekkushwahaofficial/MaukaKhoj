from app.ai.semantic.models import SemanticJobAnalysis
from app.domain.profile import Profile
from app.matching.hybrid_builder import HybridMatchEvidenceBuilder
from app.matching.models import MatchDimension, MatchResult


def make_match_result() -> MatchResult:
    dimension = MatchDimension(
        matched=False,
        evidence=("Deterministic evidence.",),
    )

    return MatchResult(
        role=dimension,
        skills=dimension,
        experience=dimension,
        education=dimension,
        location=dimension,
        remote=dimension,
        employment=dimension,
        domain=dimension,
    )


def make_profile() -> Profile:
    return Profile(
        name="Test User",
        target_titles=[
            "Software Engineer",
            "Backend Engineer",
        ],
        skills=[
            "Java",
            "Spring Boot",
            "PostgreSQL",
        ],
        locations=["India"],
        remote_preferences=["INDIA_REMOTE"],
        employment_preferences=["FULL_TIME"],
        domains=["backend", "payments"],
    )


def test_builder_preserves_deterministic_evidence_without_semantic_analysis() -> None:
    deterministic = make_match_result()

    evidence = HybridMatchEvidenceBuilder().build(
        match_result=deterministic,
        profile=make_profile(),
    )

    assert evidence.deterministic is deterministic
    assert evidence.semantic is None
    assert evidence.semantic_role_match is None
    assert evidence.semantic_skill_matches == ()
    assert evidence.semantic_domain_matches == ()
    assert evidence.semantic_evidence == ()


def test_builder_matches_semantic_role_family() -> None:
    evidence = HybridMatchEvidenceBuilder().build(
        match_result=make_match_result(),
        profile=make_profile(),
        semantic_analysis=SemanticJobAnalysis(
            job_id="job-1",
            role_family="software_engineering",
            confidence=0.9,
        ),
    )

    assert evidence.semantic_role_match is True


def test_builder_does_not_match_unknown_semantic_role_family() -> None:
    evidence = HybridMatchEvidenceBuilder().build(
        match_result=make_match_result(),
        profile=make_profile(),
        semantic_analysis=SemanticJobAnalysis(
            job_id="job-1",
            role_family="data_science",
            confidence=0.9,
        ),
    )

    assert evidence.semantic_role_match is False


def test_builder_matches_semantic_skills_against_profile() -> None:
    evidence = HybridMatchEvidenceBuilder().build(
        match_result=make_match_result(),
        profile=make_profile(),
        semantic_analysis=SemanticJobAnalysis(
            job_id="job-1",
            semantic_skills=(
                "Java",
                "Spring Boot",
                "Kafka",
            ),
            confidence=0.9,
        ),
    )

    assert evidence.semantic_skill_matches == (
        "Java",
        "Spring Boot",
    )


def test_builder_matches_semantic_domains_against_profile() -> None:
    evidence = HybridMatchEvidenceBuilder().build(
        match_result=make_match_result(),
        profile=make_profile(),
        semantic_analysis=SemanticJobAnalysis(
            job_id="job-1",
            domains=(
                "backend",
                "payments",
                "fintech",
            ),
            confidence=0.9,
        ),
    )

    assert evidence.semantic_domain_matches == (
        "backend",
        "payments",
    )


def test_builder_preserves_semantic_evidence_verbatim() -> None:
    semantic_evidence = (
        "Build backend services using Java.",
        "Work with PostgreSQL.",
    )

    evidence = HybridMatchEvidenceBuilder().build(
        match_result=make_match_result(),
        profile=make_profile(),
        semantic_analysis=SemanticJobAnalysis(
            job_id="job-1",
            evidence=semantic_evidence,
            confidence=0.9,
        ),
    )

    assert evidence.semantic_evidence == semantic_evidence


def test_builder_does_not_modify_deterministic_match_result() -> None:
    deterministic = make_match_result()

    evidence = HybridMatchEvidenceBuilder().build(
        match_result=deterministic,
        profile=make_profile(),
        semantic_analysis=SemanticJobAnalysis(
            job_id="job-1",
            role_family="software_engineering",
            semantic_skills=("Java",),
            confidence=0.95,
        ),
    )

    assert evidence.deterministic is deterministic
    assert evidence.deterministic.role.matched is False
    assert evidence.deterministic.skills.matched is False
