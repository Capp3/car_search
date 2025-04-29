"""Tests for the SearchOptionsPanel component."""

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtWidgets import QApplication

from src.car_search.ui.search_options_panel import SearchOptionsPanel


@pytest.fixture
def app():
    """Create a QApplication instance for tests."""
    return QApplication([])


@pytest.fixture
def search_options_panel():
    """Create a SearchOptionsPanel instance with mocked config manager."""
    with patch("src.car_search.ui.search_options_panel.config_manager") as mock_config:
        # Mock the get_setting method to return test values
        mock_config.get_setting.side_effect = lambda path: {
            "search.use_test_data": False,
            "search.default_radius": 50,
            "search.default_max_price": 10000,
            "search.request_delay": 1.5,
        }.get(path)

        panel = SearchOptionsPanel()
        yield panel


def test_init(app, search_options_panel):
    """Test initialization of the SearchOptionsPanel."""
    # Verify UI components exist
    assert search_options_panel.use_test_data_checkbox is not None
    assert search_options_panel.default_radius_input is not None
    assert search_options_panel.default_max_price_input is not None
    assert search_options_panel.request_delay_input is not None
    assert search_options_panel.save_button is not None

    # Verify initial values
    assert search_options_panel.use_test_data_checkbox.isChecked() is False
    assert search_options_panel.default_radius_input.value() == 50
    assert search_options_panel.default_max_price_input.value() == 10000
    assert search_options_panel.request_delay_input.value() == 1.5


def test_save_settings(app, search_options_panel):
    """Test saving settings."""
    # Mock the config manager's update_setting method
    mock_update = MagicMock()
    search_options_panel.settings_saved = MagicMock()

    with patch("src.car_search.ui.search_options_panel.config_manager.update_setting", mock_update):
        # Change some settings
        search_options_panel.use_test_data_checkbox.setChecked(True)
        search_options_panel.default_radius_input.setValue(75)
        search_options_panel.default_max_price_input.setValue(15000)
        search_options_panel.request_delay_input.setValue(2.0)

        # Save settings
        search_options_panel._save_settings()

        # Verify config manager was called with correct values
        mock_update.assert_any_call("search.use_test_data", True)
        mock_update.assert_any_call("search.default_radius", 75)
        mock_update.assert_any_call("search.default_max_price", 15000)
        mock_update.assert_any_call("search.request_delay", 2.0)

        # Verify signal was emitted with correct values
        search_options_panel.settings_saved.emit.assert_called_once()
        emitted_data = search_options_panel.settings_saved.emit.call_args[0][0]
        assert emitted_data["use_test_data"] is True
        assert emitted_data["default_radius"] == 75
        assert emitted_data["default_max_price"] == 15000
        assert emitted_data["request_delay"] == 2.0


def test_get_current_settings(app, search_options_panel):
    """Test getting current settings."""
    # Change some settings
    search_options_panel.use_test_data_checkbox.setChecked(True)
    search_options_panel.default_radius_input.setValue(75)
    search_options_panel.default_max_price_input.setValue(15000)
    search_options_panel.request_delay_input.setValue(2.0)

    # Get current settings
    settings = search_options_panel.get_current_settings()

    # Verify settings
    assert settings["use_test_data"] is True
    assert settings["default_radius"] == 75
    assert settings["default_max_price"] == 15000
    assert settings["request_delay"] == 2.0
