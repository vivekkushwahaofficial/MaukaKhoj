import logging

from app.logging_config import configure_logging


def test_configure_logging_sets_level():
    configure_logging(logging.DEBUG)

    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG


def test_configure_logging_adds_handler_when_none_exists():
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers.copy()

    try:
        root_logger.handlers.clear()

        configure_logging()

        assert root_logger.handlers
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
