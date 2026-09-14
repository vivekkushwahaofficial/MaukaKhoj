from app.application import MaukaKhojApplication
from app.domain.profile import Profile


def make_profile() -> Profile:
    return Profile(
        name="Test User",
        target_titles=["Backend Developer"],
        skills=["Java", "Spring Boot"],
        locations=["India"],
        remote_preferences=[
            "INDIA_REMOTE",
            "COUNTRY_REMOTE",
            "WORLDWIDE_REMOTE",
        ],
        employment_preferences=[
            "FULL_TIME",
            "INTERNSHIP",
        ],
        domains=[
            "Backend Development",
            "Software Engineering",
        ],
    )


def test_application_creates_lever_pipeline() -> None:
    application = MaukaKhojApplication(
        lever_account_name="drivetrain",
    )

    try:
        result = application.run(
            make_profile(),
            limit=6,
        )
    finally:
        application.close()

    assert result.processed_jobs
    assert result.source_failures == ()
