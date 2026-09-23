from app.ai.semantic.models import SemanticJobAnalysis
from app.matching.hybrid import HybridMatchEvidence
from app.matching.models import MatchDimension, MatchResult


def make_match_result() -> MatchResult:
    dimension = MatchDimension(
        matched=None,
        evidence=("Unknown.",),
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


def test_hybrid_match_evidence_keeps_deterministic_match() -> None:
    deterministic = make_match_result()

    evidence = HybridMatchEvidence(
        deterministic=deterministic,
    )

    assert evidence.deterministic is deterministic
    assert evidence.semantic is None
    assert evidence.semantic_role_match is None
    assert evidence.semantic_skill_matches == ()
    assert evidence.semantic_domain_matches == ()


def test_hybrid_match_evidence_can_include_semantic_analysis() -> None:
    deterministic = make_match_result()

    semantic = SemanticJobAnalysis(
        job_id="job-1",
        role_family="software_engineering",
        semantic_skills=("Java", "Spring Boot"),
        domains=("backend_engineering",),
        evidence=("Build backend services using Java.",),
        confidence=0.9,
    )

    evidence = HybridMatchEvidence(
        deterministic=deterministic,
        semantic=semantic,
        semantic_role_match=True,
        semantic_skill_matches=("Java",),
        semantic_domain_matches=("backend_engineering",),
        semantic_evidence=("Build backend services using Java.",),
    )

    assert evidence.semantic is semantic
    assert evidence.semantic_role_match is True
    assert evidence.semantic_skill_matches == ("Java",)
    assert evidence.semantic_domain_matches == ("backend_engineering",)
    assert evidence.semantic_evidence == (
        "Build backend services using Java.",
    )


def test_hybrid_match_evidence_does_not_replace_deterministic_result() -> None:
    deterministic = make_match_result()

    semantic = SemanticJobAnalysis(
        job_id="job-1",
        role_family="software_engineering",
        confidence=0.95,
    )

    evidence = HybridMatchEvidence(
        deterministic=deterministic,
        semantic=semantic,
        semantic_role_match=True,
    )

    assert evidence.deterministic.role.matched is None
    assert evidence.semantic_role_match is True
