"""Tests for the configuration manager."""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.car_search.config.manager import ConfigManager


@pytest.fixture
def config_manager():
    """Fixture to create a ConfigManager instance with mocked settings."""
    with patch("src.car_search.config.manager.settings") as mock_settings:
        # Mock the settings object
        mock_settings.dict.return_value = {
            "api": {"gemini_api_key": "secret_key", "car_data_api_key": None},
            "log": {"level": "INFO"},
        }

        # Create manager with mocked default settings loading
        with patch.object(ConfigManager, "_load_default_settings"):
            manager = ConfigManager()
            yield manager


def test_get_setting(config_manager):
    """Test retrieving settings by path."""
    with patch("src.car_search.config.manager.settings") as mock_settings:
        # Set up nested attribute access
        mock_api = MagicMock()
        mock_api.gemini_api_key = "test_key"
        mock_settings.api = mock_api

        # Test retrieval
        result = config_manager.get_setting("api.gemini_api_key")
        assert result == "test_key"


def test_get_setting_nonexistent(config_manager):
    """Test retrieving non-existent setting."""
    with patch("src.car_search.config.manager.settings") as mock_settings:
        # Test retrieval of non-existent path
        result = config_manager.get_setting("nonexistent.path")
        assert result is None


def test_update_setting(config_manager):
    """Test updating setting value."""
    with patch("src.car_search.config.manager.settings") as mock_settings:
        # Set up nested attribute access
        mock_log = MagicMock()
        mock_settings.log = mock_log

        # Test update
        result = config_manager.update_setting("log.level", "DEBUG")
        assert result is True
        assert mock_log.level == "DEBUG"


def test_update_setting_nonexistent(config_manager):
    """Test updating non-existent setting."""
    result = config_manager.update_setting("nonexistent.path", "value")
    assert result is False


def test_get_all_settings(config_manager):
    """Test getting all settings with sensitive values masked."""
    result = config_manager.get_all_settings()

    # Check structure
    assert "api" in result
    assert "log" in result

    # Check masking
    assert result["api"]["gemini_api_key"] == "****"

    # Check non-sensitive values
    assert result["log"]["level"] == "INFO"


def test_mask_sensitive_values(config_manager):
    """Test masking of sensitive values."""
    test_data = {
        "api": {"gemini_api_key": "secret", "car_data_api_key": None, "base_url": "https://example.com"},
        "log": {"level": "INFO"},
    }

    result = config_manager._mask_sensitive_values(test_data)

    # Check that API keys are masked
    assert result["api"]["gemini_api_key"] == "****"

    # Check that None values are not masked
    assert result["api"]["car_data_api_key"] is None

    # Check that non-sensitive values are not masked
    assert result["api"]["base_url"] == "https://example.com"
    assert result["log"]["level"] == "INFO"


def test_load_default_settings(config_manager):
    """Test loading default settings from file."""
    # Mock file content
    mock_json = {"api": {"car_data_api_key": "default_key"}, "ui": {"theme": "dark"}}

    # Mock file existence and reading
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_json))):
            with patch.object(config_manager, "_apply_defaults") as mock_apply:
                # Call the method
                config_manager._load_default_settings()

                # Check that _apply_defaults was called with the loaded data
                mock_apply.assert_called_once_with(mock_json)


def test_load_default_settings_error(config_manager):
    """Test error handling when loading default settings."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch("builtins.print") as mock_print:
                # Call the method
                config_manager._load_default_settings()

                # Check that error was handled
                mock_print.assert_called_once()
                assert "Error loading default settings" in mock_print.call_args[0][0]


def test_apply_defaults(config_manager):
    """Test applying default values to settings."""
    defaults = {"api": {"car_data_api_key": "default_key"}, "ui": {"theme": "dark"}}

    with patch.object(config_manager, "get_setting", return_value=None):
        with patch.object(config_manager, "update_setting") as mock_update:
            # Call the method
            config_manager._apply_defaults(defaults)

            # Check that update_setting was called for each setting
            assert mock_update.call_count == 2
            mock_update.assert_any_call("api.car_data_api_key", "default_key")
            mock_update.assert_any_call("ui.theme", "dark")
