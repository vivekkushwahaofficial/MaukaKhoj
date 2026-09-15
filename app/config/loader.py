import json
from pathlib import Path
from typing import Any

import yaml

from app.domain.profile import Profile


def load_config(path: str | Path) -> dict[str, Any]:
    """Load application configuration from a YAML file."""
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("Configuration file must contain a YAML object.")

    return config


def load_profile(path: str | Path) -> Profile:
    """Load and validate a user profile from a JSON file."""
    profile_path = Path(path)

    if not profile_path.exists():
        raise FileNotFoundError(f"Profile file not found: {profile_path}")

    with profile_path.open("r", encoding="utf-8") as file:
        profile_data = json.load(file)

    if not isinstance(profile_data, dict):
        raise ValueError("Profile file must contain a JSON object.")

    return Profile.model_validate(profile_data)
