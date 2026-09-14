from unittest.mock import Mock, patch

from app.main import main


def test_main_runs_daily_digest_workflow(caplog):
    mock_application = Mock()
    mock_ai_enhancer = Mock()
    mock_email_config = Mock()
    mock_email_sender = Mock()
    mock_digest_service = Mock()

    mock_digest_service.build_digest.return_value = (
        "<html>digest</html>",
        "digest",
    )

    with (
        patch(
            "app.main.MaukaKhojApplication",
            return_value=mock_application,
        ),
        patch(
            "app.main.GeminiJobAIEnhancer.from_environment",
            return_value=mock_ai_enhancer,
        ),
        patch(
            "app.main.EmailConfig.from_environment",
            return_value=mock_email_config,
        ),
        patch(
            "app.main.EmailSender.from_config",
            return_value=mock_email_sender,
        ),
        patch(
            "app.main.DigestService",
            return_value=mock_digest_service,
        ),
        caplog.at_level("INFO"),
    ):
        main()

    assert "Starting MaukaKhoj" in caplog.text
    assert "MaukaKhoj daily digest sent successfully" in caplog.text

    mock_application.close.assert_called_once()

    mock_digest_service.build_digest.assert_called_once()

    digest_call = mock_digest_service.build_digest.call_args
    assert digest_call.kwargs["limit"] == 6

    mock_email_sender.send.assert_called_once_with(
        sender=mock_email_config.from_email,
        recipient=mock_email_config.to_email,
        subject="MaukaKhoj Daily Job Digest",
        plain_text="digest",
        html="<html>digest</html>",
    )
