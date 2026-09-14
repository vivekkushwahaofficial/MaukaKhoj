from app.domain.profile import Profile


def test_profile_can_be_created():
    profile = Profile(
        name="Candidate",
        target_titles=["Backend Developer", "Software Engineer"],
        skills=["Python", "Java", "SQL"],
        locations=["India"],
        remote_preferences=["INDIA_REMOTE"],
        domains=["Backend Development"],
    )

    assert profile.name == "Candidate"
    assert "Python" in profile.skills
    assert "Backend Developer" in profile.target_titles


def test_profile_has_safe_defaults():
    profile = Profile(name="Candidate")

    assert profile.target_titles == []
    assert profile.skills == []
    assert profile.locations == []
    assert profile.domains == []
    assert profile.experience.years == 0.0


def test_profile_rejects_empty_name():
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        Profile(name="")
