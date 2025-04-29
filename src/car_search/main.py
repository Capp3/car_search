"""Main module for the Car Search application.

This module provides the entry point for the application.
"""

import sys

from .config.manager import config_manager
from .core.logging import get_logger
from .ui.app import run_application

# Set up logger for this module
logger = get_logger(__name__)


def main():
    """Run the Car Search application."""
    logger.info("Starting Car Search application")

    # Log configuration settings (with sensitive values masked)
    settings = config_manager.get_all_settings()
    logger.debug(f"Configuration settings: {settings}")

    # Check for required API keys
    gemini_api_key = config_manager.get_setting("api.gemini_api_key")
    if not gemini_api_key:
        logger.warning("Gemini API key not set. LLM features will be unavailable.")

    # Run Qt application
    exit_code = run_application()

    # Exit with the application's exit code
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
