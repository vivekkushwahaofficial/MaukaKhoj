import logging
from pathlib import Path

from app.ai.gemini import GeminiJobAIEnhancer
from app.application import MaukaKhojApplication
from app.config.loader import load_config, load_profile
from app.delivery.digest_renderer import DigestRenderer
from app.delivery.digest_service import DigestService
from app.delivery.email_config import EmailConfig
from app.delivery.email_sender import EmailSender
from app.logging_config import configure_logging

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
PROFILE_PATH = PROJECT_ROOT / "data" / "profile.json"


def main() -> None:
    """Run the MaukaKhoj job discovery and email digest workflow."""
    configure_logging()

    logger.info("Starting MaukaKhoj")

    config = load_config(CONFIG_PATH)
    profile = load_profile(PROFILE_PATH)

    sources_config = config["sources"]
    lever_config = sources_config["lever"]
    freshness_config = config["freshness"]
    output_config = config["output"]

    application = MaukaKhojApplication(
        lever_account_name=lever_config["account_name"],
        request_timeout_seconds=float(sources_config["request_timeout_seconds"]),
        freshness_config=freshness_config,
    )

    try:
        ai_enhancer = GeminiJobAIEnhancer.from_environment()
        email_config = EmailConfig.from_environment()
        email_sender = EmailSender.from_config(email_config)

        digest_service = DigestService(
            application=application,
            renderer=DigestRenderer(),
            ai_enhancer=ai_enhancer,
        )

        html, text = digest_service.build_digest(
            profile,
            limit=int(output_config["max_jobs_per_digest"]),
        )

        email_sender.send(
            sender=email_config.from_email,
            recipient=email_config.to_email,
            subject="MaukaKhoj Daily Job Digest",
            plain_text=text,
            html=html,
        )

        logger.info(
            "MaukaKhoj daily digest sent successfully for profile '%s'",
            profile.name,
        )
    finally:
        application.close()


if __name__ == "__main__":
    main()
