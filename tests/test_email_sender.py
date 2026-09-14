from unittest.mock import MagicMock, patch

import pytest

from app.delivery.email_sender import EmailSender


def make_sender() -> EmailSender:
    return EmailSender(
        smtp_host="smtp.example.com",
        smtp_port=465,
        username="sender@example.com",
        password="secret",
    )


@patch("app.delivery.email_sender.smtplib.SMTP_SSL")
def test_send_email(mock_smtp: MagicMock) -> None:
    smtp = mock_smtp.return_value.__enter__.return_value

    sender = EmailSender(
        smtp_host="smtp.zoho.in",
        smtp_port=465,
        username="sender@example.com",
        password="secret",
    )

    sender.send(
        sender="sender@example.com",
        recipient="recipient@example.com",
        subject="MaukaKhoj Job Digest",
        plain_text="Plain text digest",
        html="<h1>HTML digest</h1>",
    )

    mock_smtp.assert_called_once_with(
        "smtp.zoho.in",
        465,
    )

    smtp.ehlo.assert_called_once()
    smtp.login.assert_called_once_with(
        "sender@example.com",
        "secret",
    )

    smtp.send_message.assert_called_once()

    message = smtp.send_message.call_args.args[0]

    assert message["From"] == "sender@example.com"
    assert message["To"] == "recipient@example.com"
    assert message["Subject"] == "MaukaKhoj Job Digest"

    body = message.as_string()

    assert "Plain text digest" in body
    assert "<h1>HTML digest</h1>" in body


@patch("app.delivery.email_sender.smtplib.SMTP")
def test_send_email_with_starttls(mock_smtp: MagicMock) -> None:
    smtp = mock_smtp.return_value.__enter__.return_value

    sender = EmailSender(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="sender@example.com",
        password="secret",
        use_tls=True,
    )

    sender.send(
        sender="sender@example.com",
        recipient="recipient@example.com",
        subject="MaukaKhoj Job Digest",
        plain_text="Plain text digest",
        html="<h1>HTML digest</h1>",
    )

    mock_smtp.assert_called_once_with(
        "smtp.example.com",
        587,
    )

    smtp.ehlo.assert_any_call()
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with(
        "sender@example.com",
        "secret",
    )
    smtp.send_message.assert_called_once()


def test_empty_smtp_host_rejected() -> None:
    with pytest.raises(ValueError, match="SMTP host"):
        EmailSender(
            smtp_host="",
            smtp_port=465,
            username="sender@example.com",
            password="secret",
        )


def test_invalid_smtp_port_rejected() -> None:
    with pytest.raises(ValueError, match="SMTP port"):
        EmailSender(
            smtp_host="smtp.example.com",
            smtp_port=0,
            username="sender@example.com",
            password="secret",
        )


def test_empty_username_rejected() -> None:
    with pytest.raises(ValueError, match="SMTP username"):
        EmailSender(
            smtp_host="smtp.example.com",
            smtp_port=465,
            username="",
            password="secret",
        )


def test_empty_password_rejected() -> None:
    with pytest.raises(ValueError, match="SMTP password"):
        EmailSender(
            smtp_host="smtp.example.com",
            smtp_port=465,
            username="sender@example.com",
            password="",
        )


def test_empty_sender_rejected() -> None:
    with pytest.raises(ValueError, match="Sender email"):
        make_sender().send(
            sender="",
            recipient="recipient@example.com",
            subject="Test",
            plain_text="Text",
            html="<p>HTML</p>",
        )


def test_empty_recipient_rejected() -> None:
    with pytest.raises(ValueError, match="Recipient email"):
        make_sender().send(
            sender="sender@example.com",
            recipient="",
            subject="Test",
            plain_text="Text",
            html="<p>HTML</p>",
        )


def test_empty_subject_rejected() -> None:
    with pytest.raises(ValueError, match="Email subject"):
        make_sender().send(
            sender="sender@example.com",
            recipient="recipient@example.com",
            subject="",
            plain_text="Text",
            html="<p>HTML</p>",
        )


def test_create_sender_from_config(monkeypatch) -> None:
    from app.delivery.email_config import EmailConfig

    monkeypatch.setenv("SMTP_HOST", "smtp.zoho.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USER", "sender@zohomail.in")
    monkeypatch.setenv("SMTP_PASS", "secret")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("MAIL_TO", "recipient@example.com")

    config = EmailConfig.from_environment()
    sender = EmailSender.from_config(config)

    assert sender._smtp_host == "smtp.zoho.com"
    assert sender._smtp_port == 465
    assert sender._username == "sender@zohomail.in"
    assert sender._password == "secret"
    assert sender._use_tls is True
