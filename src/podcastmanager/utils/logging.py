"""
Logging configuration using loguru.

This module sets up application-wide logging with support for
console and file output, log rotation, and proper formatting.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    rotation: str = "10 MB",
    retention: str = "1 week",
    colorize: bool = True,
) -> None:
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, only console logging is enabled
        rotation: Log file rotation size or time (e.g., "10 MB", "1 day")
        retention: How long to keep old log files (e.g., "1 week", "30 days")
        colorize: Whether to colorize console output
    """
    # Remove default logger
    logger.remove()

    # Add console handler with colors
    logger.add(
        sys.stderr,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=colorize,
    )

    # Add file handler if log file is specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_file),
            level=log_level,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            rotation=rotation,
            retention=retention,
            compression="zip",  # Compress old log files
            enqueue=True,  # Thread-safe logging
        )
        logger.info(f"Logging to file: {log_file}")

    logger.info(f"Logging initialized at {log_level} level")


def get_logger(name: str = None):
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance from loguru

    Note:
        In most cases, you can just import logger directly from loguru:
        `from loguru import logger`
    """
    if name:
        return logger.bind(name=name)
    return logger
