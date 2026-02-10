"""Unified logging configuration.

Replaces duplicated logging.basicConfig() calls across 4+ services.
"""
import logging
import sys


def setup_logging(
    service_name: str,
    level: str = "INFO",
    fmt: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> logging.Logger:
    """Configure logging for a service and return the logger.

    Args:
        service_name: Name used as the logger identifier.
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
        fmt: Log message format string.

    Returns:
        Configured logger instance.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format=fmt, stream=sys.stdout)
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)
    logger.info(f"Logging initialized for {service_name} at level {level}")
    return logger
