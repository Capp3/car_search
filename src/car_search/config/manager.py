"""Configuration manager for the Car Search application.

This module provides a manager class for accessing and updating application settings.
It handles default settings, runtime configuration updates, and provides a clean
interface for the rest of the application to interact with configuration.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .settings import CONFIG_DIR, PROJECT_ROOT, settings


class ConfigManager:
    """Manages configuration for the Car Search application.

    Provides methods for accessing and updating settings, handling
    default values, and masking sensitive information.
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self.config_dir = CONFIG_DIR
        self.default_config_path = self.config_dir / "default_settings.json"
        self._load_default_settings()

    def _load_default_settings(self) -> None:
        """Load default settings from file if it exists."""
        if self.default_config_path.exists():
            try:
                with open(self.default_config_path, "r") as f:
                    defaults = json.load(f)
                    self._apply_defaults(defaults)
            except (json.JSONDecodeError, IOError) as e:
                # Log the error but continue with default values
                print(f"Error loading default settings: {e}")

    def _apply_defaults(self, defaults: Dict[str, Any], prefix: str = "") -> None:
        """Apply default values recursively to settings.

        Args:
            defaults: Dictionary of default values
            prefix: Prefix for nested settings access
        """
        for key, value in defaults.items():
            path = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # Recurse into nested dictionaries
                self._apply_defaults(value, path)
            else:
                # Only apply default if the setting is not already set
                if self.get_setting(path) is None:
                    self.update_setting(path, value)

    def get_setting(self, path: str) -> Any:
        """Get a setting value by dot-notation path.

        Args:
            path: Dot-notation path to the setting
                (e.g., "api.gemini_api_key")

        Returns:
            The setting value or None if not found
        """
        parts = path.split(".")
        current = settings

        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None

        return current

    def update_setting(self, path: str, value: Any) -> bool:
        """Update a setting value by dot-notation path.

        Note: This updates runtime settings but does not persist to environment.

        Args:
            path: Dot-notation path to the setting
                (e.g., "log.level")
            value: New value for the setting

        Returns:
            True if the setting was updated, False otherwise
        """
        parts = path.split(".")
        current = settings

        # Navigate to the parent object
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return False

        # Update the value if the final attribute exists
        if hasattr(current, parts[-1]):
            setattr(current, parts[-1], value)
            return True

        return False

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary with sensitive values masked.

        Returns:
            Dictionary of all settings
        """
        settings_dict = settings.dict()
        return self._mask_sensitive_values(settings_dict)

    def _mask_sensitive_values(self, data: Dict[str, Any], path: str = "") -> Dict[str, Any]:
        """Recursively mask sensitive values in the settings dictionary.

        Args:
            data: Dictionary to mask values in
            path: Current path in the dictionary

        Returns:
            Dictionary with sensitive values masked
        """
        result = {}

        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            if isinstance(value, dict):
                # Recurse into nested dictionaries
                result[key] = self._mask_sensitive_values(value, current_path)
            elif "api_key" in key and value:
                # Mask API keys that are set
                result[key] = "****"
            else:
                result[key] = value

        return result

    def save_default_settings(self) -> bool:
        """Save current non-sensitive settings as default settings.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure config directory exists
            os.makedirs(self.config_dir, exist_ok=True)

            # Get settings with sensitive values masked
            settings_dict = self.get_all_settings()

            # Save to default settings file
            with open(self.default_config_path, "w") as f:
                json.dump(settings_dict, f, indent=2)

            return True
        except (IOError, OSError) as e:
            # Log the error
            print(f"Error saving default settings: {e}")
            return False


# Create and export singleton config manager instance
config_manager = ConfigManager()
