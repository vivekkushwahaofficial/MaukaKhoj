import logging
from pathlib import Path

from app.config.loader import load_config, load_profile
from app.logging_config import configure_logging


logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
PROFILE_PATH = PROJECT_ROOT / "data" / "profile.json"


def main() -> None:
    """Initialize the MaukaKhoj application."""
    configure_logging()

    logger.info("Starting MaukaKhoj")

    config = load_config(CONFIG_PATH)
    profile = load_profile(PROFILE_PATH)

    logger.info(
        "MaukaKhoj initialized successfully for profile '%s'",
        profile.name,
    )

    # Keep these objects available for the next application layer.
    _ = config
    _ = profile


if __name__ == "__main__":
    main()
