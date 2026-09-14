import json

import pytest
from pydantic import ValidationError

from app.config.loader import load_config, load_profile


def test_load_config():
    config = load_config("config/config.yaml")

    assert config["app"]["name"] == "MaukaKhoj"
    assert config["app"]["environment"] == "development"
    assert config["matching"]["skills_weight"] == 30


def test_load_profile():
    profile = load_profile("data/profile.json")

    assert profile.name == "Candidate"
    assert "Java" in profile.skills
    assert "Backend Developer" in profile.target_titles


def test_load_config_rejects_missing_file(tmp_path):
    missing_file = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        load_config(missing_file)


def test_load_profile_rejects_missing_file(tmp_path):
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_profile(missing_file)


def test_load_config_rejects_non_object(tmp_path):
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="YAML object"):
        load_config(config_file)


def test_load_profile_rejects_non_object(tmp_path):
    profile_file = tmp_path / "invalid.json"
    profile_file.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        load_profile(profile_file)


def test_load_profile_rejects_invalid_profile(tmp_path):
    profile_file = tmp_path / "invalid.json"
    profile_file.write_text(
        json.dumps(
            {
                "name": "",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_profile(profile_file)
