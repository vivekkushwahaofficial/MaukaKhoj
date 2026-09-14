from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.delivery.email_config import EmailConfig


class EmailSender:
    """Send rendered email content through an SMTP server."""

    def __init__(
        self,
        *,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
    ) -> None:
        if not smtp_host.strip():
            raise ValueError("SMTP host cannot be empty.")

        if smtp_port <= 0:
            raise ValueError("SMTP port must be greater than zero.")

        if not username.strip():
            raise ValueError("SMTP username cannot be empty.")

        if not password:
            raise ValueError("SMTP password cannot be empty.")

        self._smtp_host = smtp_host.strip()
        self._smtp_port = smtp_port
        self._username = username.strip()
        self._password = password
        self._use_tls = use_tls

    @classmethod
    def from_config(cls, config: EmailConfig) -> "EmailSender":
        """Create an EmailSender from email configuration."""
        return cls(
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            username=config.smtp_username,
            password=config.smtp_password,
            use_tls=config.smtp_use_tls,
        )

    def send(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        plain_text: str,
        html: str,
    ) -> None:
        """Send a multipart plain-text and HTML email."""
        if not sender.strip():
            raise ValueError("Sender email cannot be empty.")

        if not recipient.strip():
            raise ValueError("Recipient email cannot be empty.")

        if not subject.strip():
            raise ValueError("Email subject cannot be empty.")

        message = EmailMessage()
        message["From"] = sender.strip()
        message["To"] = recipient.strip()
        message["Subject"] = subject.strip()

        message.set_content(plain_text)
        message.add_alternative(html, subtype="html")

        if self._smtp_port == 465:
            self._send_with_ssl(message)
        else:
            self._send_with_starttls(message)

    def _send_with_ssl(self, message: EmailMessage) -> None:
        """Send using implicit SSL, normally used on port 465."""
        with smtplib.SMTP_SSL(
            self._smtp_host,
            self._smtp_port,
        ) as smtp:
            smtp.ehlo()
            smtp.login(
                self._username,
                self._password,
            )
            smtp.send_message(message)

    def _send_with_starttls(self, message: EmailMessage) -> None:
        """Send using STARTTLS, normally used on port 587."""
        with smtplib.SMTP(
            self._smtp_host,
            self._smtp_port,
        ) as smtp:
            smtp.ehlo()

            if self._use_tls:
                smtp.starttls()
                smtp.ehlo()

            smtp.login(
                self._username,
                self._password,
            )

            smtp.send_message(message)
