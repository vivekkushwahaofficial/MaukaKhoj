import pytest

from app.delivery.email_config import EmailConfig


def set_valid_environment(monkeypatch) -> None:
    monkeypatch.setenv("SMTP_HOST", "smtp.zoho.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "sender@zohomail.in")
    monkeypatch.setenv("SMTP_PASS", "secret")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("MAIL_TO", "recipient@example.com")


def test_load_valid_configuration(monkeypatch) -> None:
    set_valid_environment(monkeypatch)

    config = EmailConfig.from_environment()

    assert config.smtp_host == "smtp.zoho.com"
    assert config.smtp_port == 465
    assert config.smtp_username == "sender@zohomail.in"
    assert config.smtp_password == "secret"
    assert config.smtp_use_tls is True
    assert config.from_email == "sender@zohomail.in"
    assert config.to_email == "recipient@example.com"


def test_missing_required_variable(monkeypatch) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.delenv("SMTP_HOST")

    with pytest.raises(
        ValueError,
        match="SMTP_HOST",
    ):
        EmailConfig.from_environment()


def test_invalid_port(monkeypatch) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("SMTP_PORT", "invalid")

    with pytest.raises(
        ValueError,
        match="SMTP_PORT",
    ):
        EmailConfig.from_environment()


def test_non_positive_port(monkeypatch) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("SMTP_PORT", "0")

    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        EmailConfig.from_environment()


def test_tls_defaults_to_true(monkeypatch) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.delenv("SMTP_USE_TLS")

    config = EmailConfig.from_environment()

    assert config.smtp_use_tls is True


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("0", False),
        ("no", False),
        ("off", False),
    ],
)
def test_tls_boolean_values(
    monkeypatch,
    value: str,
    expected: bool,
) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("SMTP_USE_TLS", value)

    config = EmailConfig.from_environment()

    assert config.smtp_use_tls is expected


def test_invalid_tls_value(monkeypatch) -> None:
    set_valid_environment(monkeypatch)
    monkeypatch.setenv("SMTP_USE_TLS", "maybe")

    with pytest.raises(
        ValueError,
        match="SMTP_USE_TLS",
    ):
        EmailConfig.from_environment()
