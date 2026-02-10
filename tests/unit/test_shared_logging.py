"""Unit tests for shared.logging module."""
import logging
from shared.logging import setup_logging


class TestSetupLogging:
    def test_returns_logger(self):
        logger = setup_logging("test-service")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test-service"

    def test_log_level_info(self):
        logger = setup_logging("test-info", level="INFO")
        assert logger.level == logging.INFO

    def test_log_level_debug(self):
        logger = setup_logging("test-debug", level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_log_level_case_insensitive(self):
        logger = setup_logging("test-case", level="warning")
        assert logger.level == logging.WARNING
