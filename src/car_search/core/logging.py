"""Logging configuration for the Car Search application.

This module sets up logging for the application, using settings from the configuration system.
"""

import logging
import os

from ..config.settings import settings


def setup_logger(name: str = None) -> logging.Logger:
    """Set up and configure a logger instance.

    Args:
        name: Logger name, defaults to root logger if None

    Returns:
        Configured logger instance
    """
    # Get logger
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Set log level from settings
        log_level = getattr(logging, settings.log.level.upper())
        logger.setLevel(log_level)

        # Create formatters
        formatter = logging.Formatter(settings.log.format)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Create file handler
        log_dir = settings.log.dir
        os.makedirs(log_dir, exist_ok=True)

        # Use logger name in file name if provided
        if name:
            log_file = log_dir / f"{name.lower()}.log"
        else:
            log_file = log_dir / settings.log.file_name

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logger initialized: {name or 'root'}")

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance by name.

    Args:
        name: Logger name, defaults to root logger if None

    Returns:
        Logger instance
    """
    return setup_logger(name)


# Configure the root logger
root_logger = setup_logger()
