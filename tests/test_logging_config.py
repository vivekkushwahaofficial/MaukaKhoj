import logging

from app.logging_config import configure_logging


def test_configure_logging_sets_level():
    configure_logging(logging.DEBUG)

    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG


def test_configure_logging_sets_handler():
    configure_logging()

    root_logger = logging.getLogger()

    assert root_logger.handlers
