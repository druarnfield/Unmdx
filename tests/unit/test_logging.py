"""Unit tests for logging utilities."""

import logging
from pathlib import Path
import tempfile

from unmdx.utils.logging import get_logger, setup_logging


class TestLogging:
    """Test logging utility functions."""

    def test_setup_logging_default(self):
        """Test default logging setup."""
        logger = setup_logging()

        assert logger.name == "unmdx"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logging_debug_level(self):
        """Test logging setup with debug level."""
        logger = setup_logging(level="DEBUG")

        assert logger.level == logging.DEBUG

    def test_setup_logging_with_file(self):
        """Test logging setup with file output."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "test.log"
            logger = setup_logging(log_file=log_file)

            assert len(logger.handlers) == 2
            assert log_file.exists()

            # Test that file handler exists
            file_handler = next(
                (h for h in logger.handlers if isinstance(h, logging.FileHandler)),
                None
            )
            assert file_handler is not None

    def test_setup_logging_custom_format(self):
        """Test logging setup with custom format."""
        custom_format = "%(levelname)s: %(message)s"
        logger = setup_logging(format_string=custom_format)

        formatter = logger.handlers[0].formatter
        assert formatter._fmt == custom_format

    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test_module")

        assert logger.name == "unmdx.test_module"
        assert isinstance(logger, logging.Logger)

    def test_logging_levels(self):
        """Test different logging levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            logger = setup_logging(level=level)
            assert logger.level == getattr(logging, level)

    def test_log_file_directory_creation(self):
        """Test that log file directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "nested" / "dir" / "test.log"
            setup_logging(log_file=log_file)

            assert log_file.parent.exists()
            assert log_file.exists()

    def test_logger_hierarchy(self):
        """Test that child loggers inherit configuration."""
        parent_logger = setup_logging()
        child_logger = get_logger("child")

        # Child should inherit level from parent
        assert child_logger.getEffectiveLevel() == parent_logger.level
