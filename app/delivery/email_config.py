from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class EmailConfig:
    """SMTP and digest email configuration."""

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    from_email: str
    to_email: str

    @classmethod
    def from_environment(cls) -> "EmailConfig":
        """Load email configuration from environment variables."""
        return cls(
            smtp_host=_required("SMTP_HOST"),
            smtp_port=_required_int("SMTP_PORT"),
            smtp_username=_required("SMTP_USER"),
            smtp_password=_required("SMTP_PASS"),
            smtp_use_tls=_boolean("SMTP_USE_TLS", default=True),
            from_email=_required("SMTP_USER"),
            to_email=_required("MAIL_TO"),
        )


def _required(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise ValueError(f"Required environment variable '{name}' is missing.")

    return value.strip()


def _required_int(name: str) -> int:
    value = _required(name)

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable '{name}' must be an integer.") from exc

    if parsed <= 0:
        raise ValueError(f"Environment variable '{name}' must be greater than zero.")

    return parsed


def _boolean(name: str, *, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"true", "1", "yes", "on"}:
        return True

    if normalized in {"false", "0", "no", "off"}:
        return False

    raise ValueError(f"Environment variable '{name}' must be a boolean.")
