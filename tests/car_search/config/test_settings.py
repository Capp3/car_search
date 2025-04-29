"""Tests for the settings module."""

import os
from pathlib import Path
from unittest.mock import patch

from src.car_search.config.settings import (
    APISettings,
    AppSettings,
    LogSettings,
    SearchSettings,
    UISettings,
)


def test_log_settings_defaults():
    """Test default values for LogSettings."""
    log_settings = LogSettings()
    assert log_settings.level == "INFO"
    assert "%(asctime)s" in log_settings.format
    assert isinstance(log_settings.dir, Path)


def test_api_settings_defaults():
    """Test default values for APISettings."""
    api_settings = APISettings()
    assert api_settings.autotrader_base_url == "https://www.autotrader.co.uk"
    assert api_settings.gemini_api_key is None
    assert api_settings.car_data_api_key is None
    assert api_settings.edmunds_api_key is None


def test_ui_settings_defaults():
    """Test default values for UISettings."""
    ui_settings = UISettings()
    assert ui_settings.theme == "system"
    assert ui_settings.font_size == 12
    assert ui_settings.max_results_per_page == 20


def test_search_settings_defaults():
    """Test default values for SearchSettings."""
    search_settings = SearchSettings()
    assert search_settings.default_radius == 50
    assert search_settings.default_max_price == 10000
    assert search_settings.request_delay == 1.5
    assert search_settings.cache_expiry == 3600
    assert search_settings.use_test_data is False


def test_app_settings_composition():
    """Test that AppSettings correctly composes all settings."""
    app_settings = AppSettings()
    assert isinstance(app_settings.log, LogSettings)
    assert isinstance(app_settings.api, APISettings)
    assert isinstance(app_settings.ui, UISettings)
    assert isinstance(app_settings.search, SearchSettings)
    assert app_settings.debug is False


@patch.dict(os.environ, {"API_GEMINI_API_KEY": "test_gemini_key", "LOG_LEVEL": "DEBUG", "DEBUG": "true"})
def test_environment_variable_override():
    """Test that environment variables override default values."""
    app_settings = AppSettings()
    assert app_settings.api.gemini_api_key == "test_gemini_key"
    assert app_settings.log.level == "DEBUG"
    assert app_settings.debug is True


def test_log_dir_creation():
    """Test that the log directory is created if it doesn't exist."""
    with patch("os.makedirs") as mock_makedirs:
        log_settings = LogSettings(dir=Path("/tmp/nonexistent/logs"))
        mock_makedirs.assert_called_once_with(Path("/tmp/nonexistent/logs"), exist_ok=True)
