from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.application import MaukaKhojApplication
from app.domain.profile import Profile


def make_profile() -> Profile:
    """Create a minimal profile suitable for application-level tests."""
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


def make_job(
    *,
    job_id: str,
    posted_at: datetime | None,
) -> dict:
    """Create a realistic raw Lever job payload for application tests."""
    created_at = int(posted_at.timestamp() * 1000) if posted_at is not None else None

    return {
        "id": job_id,
        "text": "Backend Developer",
        "descriptionPlain": ("Backend engineering role using Java and Spring Boot."),
        "categories": {
            "location": "India",
            "commitment": "Full-time",
        },
        "workplaceType": "remote",
        "createdAt": created_at,
        "hostedUrl": f"https://example.com/jobs/{job_id}",
        "applyUrl": f"https://example.com/apply/{job_id}",
    }


def test_application_creates_lever_pipeline() -> None:
    """Verify the application wires the Lever source into the pipeline."""
    jobs = [
        make_job(
            job_id="job-1",
            posted_at=datetime.now(timezone.utc),
        ),
    ]

    with patch(
        "app.application.LeverAdapter.fetch_jobs",
        return_value=jobs,
    ):
        application = MaukaKhojApplication(
            sources_config={
                "lever": {
                    "account_name": "drivetrain",
                },
            },
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


def test_application_accepts_freshness_configuration() -> None:
    """Verify application-level freshness filtering works end-to-end."""
    fresh_job = make_job(
        job_id="job-fresh",
        posted_at=datetime.now(timezone.utc) - timedelta(days=10),
    )

    stale_job = make_job(
        job_id="job-stale",
        posted_at=datetime.now(timezone.utc) - timedelta(days=31),
    )

    with patch(
        "app.application.LeverAdapter.fetch_jobs",
        return_value=[fresh_job, stale_job],
    ):
        application = MaukaKhojApplication(
            sources_config={
                "lever": {
                    "account_name": "drivetrain",
                },
            },
            freshness_config={
                "enabled": True,
                "max_age_days": 30,
            },
        )

        try:
            result = application.run(
                make_profile(),
                limit=6,
            )
        finally:
            application.close()

    assert [item.job.job_id for item in result.processed_jobs] == [
        "lever:drivetrain:job-fresh",
    ]

    assert len(result.rejected_jobs) == 1
    assert result.rejected_jobs[0].job.job_id == "lever:drivetrain:job-stale"


def test_application_registers_lever_source() -> None:
    """Verify the configured Lever source can be constructed."""
    application = MaukaKhojApplication(
        sources_config={
            "lever": {
                "account_name": "drivetrain",
            },
        },
    )

    try:
        assert application is not None
    finally:
        application.close()
