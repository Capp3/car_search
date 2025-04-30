"""Search options panel for the Car Search application.

This module provides a panel for configuring search-related settings.
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config.manager import config_manager
from ..core.logging import get_logger

# Set up logger for this module
logger = get_logger(__name__)


class SearchOptionsPanel(QWidget):
    """Panel for configuring search options and settings."""

    # Signal emitted when settings are saved
    settings_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        """Initialize the search options panel."""
        super().__init__(parent)

        # Log initialization
        logger.info("Initializing search options panel")

        # Initialize UI components
        self._init_ui()

        # Load current settings
        self._load_settings()

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Search Options")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Search behavior group
        behavior_group = QGroupBox("Search Behavior")
        behavior_layout = QVBoxLayout(behavior_group)

        # Test data option
        self.use_test_data_checkbox = QCheckBox("Use test data when real results cannot be found")
        self.use_test_data_checkbox.setToolTip(
            "When enabled, the application will show test car listings if the search provider "
            "cannot retrieve real results. This is useful for testing or when the service is down."
        )
        behavior_layout.addWidget(self.use_test_data_checkbox)

        # Playwright option
        self.use_playwright_checkbox = QCheckBox("Use Playwright for browser automation (experimental)")
        self.use_playwright_checkbox.setToolTip(
            "When enabled, the application will use Playwright for browser automation instead of "
            "HTTP requests. This can help navigate JavaScript-heavy websites but requires more resources."
        )
        self.use_playwright_checkbox.stateChanged.connect(self._on_use_playwright_changed)
        behavior_layout.addWidget(self.use_playwright_checkbox)

        layout.addWidget(behavior_group)

        # Playwright configuration group
        self.playwright_group = QGroupBox("Playwright Configuration")
        playwright_layout = QFormLayout(self.playwright_group)

        # Headless mode
        self.headless_checkbox = QCheckBox()
        self.headless_checkbox.setToolTip(
            "When enabled, the browser will run in headless mode (no visible UI). "
            "This is more efficient but may not work with some websites."
        )
        playwright_layout.addRow("Headless Mode:", self.headless_checkbox)

        # Screenshot enabled
        self.screenshot_checkbox = QCheckBox()
        self.screenshot_checkbox.setToolTip(
            "When enabled, the application will take screenshots during the automation process. "
            "This is useful for debugging but will consume more disk space."
        )
        playwright_layout.addRow("Enable Screenshots:", self.screenshot_checkbox)

        # Debug mode
        self.debug_checkbox = QCheckBox()
        self.debug_checkbox.setToolTip(
            "When enabled, the application will log additional debug information during the automation process."
        )
        playwright_layout.addRow("Debug Mode:", self.debug_checkbox)

        # Timeout
        self.timeout_input = QSpinBox()
        self.timeout_input.setRange(10, 120)
        self.timeout_input.setSingleStep(5)
        self.timeout_input.setValue(30)
        self.timeout_input.setToolTip(
            "Timeout for Playwright operations in seconds. Increase this value if you're experiencing timeouts."
        )
        playwright_layout.addRow("Timeout (seconds):", self.timeout_input)

        # Slow motion delay
        self.slow_mo_input = QSpinBox()
        self.slow_mo_input.setRange(0, 1000)
        self.slow_mo_input.setSingleStep(50)
        self.slow_mo_input.setValue(0)
        self.slow_mo_input.setSpecialValueText("Disabled")
        self.slow_mo_input.setToolTip(
            "Slow down Playwright operations by the specified amount (in milliseconds). "
            "This is useful for debugging or watching the automation process."
        )
        playwright_layout.addRow("Slow Motion Delay (ms):", self.slow_mo_input)

        layout.addWidget(self.playwright_group)

        # Search parameters group
        params_group = QGroupBox("Search Parameters")
        params_layout = QFormLayout(params_group)

        # Default radius
        self.default_radius_input = QSpinBox()
        self.default_radius_input.setRange(5, 200)
        self.default_radius_input.setSingleStep(5)
        self.default_radius_input.setValue(50)
        params_layout.addRow("Default Search Radius (miles):", self.default_radius_input)

        # Default max price
        self.default_max_price_input = QSpinBox()
        self.default_max_price_input.setRange(1000, 100000)
        self.default_max_price_input.setSingleStep(1000)
        self.default_max_price_input.setValue(10000)
        params_layout.addRow("Default Maximum Price (£):", self.default_max_price_input)

        # Request delay
        self.request_delay_input = QDoubleSpinBox()
        self.request_delay_input.setRange(0.5, 5.0)
        self.request_delay_input.setSingleStep(0.1)
        self.request_delay_input.setValue(1.5)
        self.request_delay_input.setToolTip(
            "Delay between search requests in seconds. Increase this value if you're experiencing rate limiting."
        )
        params_layout.addRow("Request Delay (seconds):", self.request_delay_input)

        layout.addWidget(params_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        # Add spacer to push content to the top
        layout.addStretch(1)

        # Initial state
        self._on_use_playwright_changed()

    def _on_use_playwright_changed(self):
        """Handle changes to the use_playwright checkbox."""
        is_enabled = self.use_playwright_checkbox.isChecked()
        self.playwright_group.setEnabled(is_enabled)

    def _load_settings(self):
        """Load current search settings from config."""
        try:
            # Load use_test_data setting
            use_test_data = config_manager.get_setting("search.use_test_data")
            self.use_test_data_checkbox.setChecked(bool(use_test_data))

            # Load use_playwright setting
            use_playwright = config_manager.get_setting("search.use_playwright")
            self.use_playwright_checkbox.setChecked(bool(use_playwright))

            # Load Playwright settings
            headless = config_manager.get_setting("playwright.headless")
            self.headless_checkbox.setChecked(bool(headless))

            screenshot_enabled = config_manager.get_setting("playwright.screenshot_enabled")
            self.screenshot_checkbox.setChecked(bool(screenshot_enabled))

            debug_mode = config_manager.get_setting("playwright.debug_mode")
            self.debug_checkbox.setChecked(bool(debug_mode))

            timeout = config_manager.get_setting("playwright.timeout")
            if timeout is not None:
                self.timeout_input.setValue(timeout)

            slow_mo = config_manager.get_setting("playwright.slow_mo")
            if slow_mo is not None:
                self.slow_mo_input.setValue(slow_mo)

            # Load default radius
            default_radius = config_manager.get_setting("search.default_radius")
            if default_radius is not None:
                self.default_radius_input.setValue(default_radius)

            # Load default max price
            default_max_price = config_manager.get_setting("search.default_max_price")
            if default_max_price is not None:
                self.default_max_price_input.setValue(default_max_price)

            # Load request delay
            request_delay = config_manager.get_setting("search.request_delay")
            if request_delay is not None:
                self.request_delay_input.setValue(request_delay)

            # Update UI state
            self._on_use_playwright_changed()

            logger.debug("Loaded search settings from config")
        except Exception as e:
            logger.error(f"Error loading search settings: {e}")

    def _save_settings(self):
        """Save search settings to config."""
        try:
            # Update use_test_data setting
            use_test_data = self.use_test_data_checkbox.isChecked()
            config_manager.update_setting("search.use_test_data", use_test_data)

            # Update use_playwright setting
            use_playwright = self.use_playwright_checkbox.isChecked()
            config_manager.update_setting("search.use_playwright", use_playwright)

            # Update Playwright settings
            config_manager.update_setting("playwright.headless", self.headless_checkbox.isChecked())
            config_manager.update_setting("playwright.screenshot_enabled", self.screenshot_checkbox.isChecked())
            config_manager.update_setting("playwright.debug_mode", self.debug_checkbox.isChecked())
            config_manager.update_setting("playwright.timeout", self.timeout_input.value())

            # Only set slow_mo if it's not zero (disabled)
            slow_mo = self.slow_mo_input.value()
            if slow_mo > 0:
                config_manager.update_setting("playwright.slow_mo", slow_mo)
            else:
                config_manager.update_setting("playwright.slow_mo", None)

            # Update default radius
            default_radius = self.default_radius_input.value()
            config_manager.update_setting("search.default_radius", default_radius)

            # Update default max price
            default_max_price = self.default_max_price_input.value()
            config_manager.update_setting("search.default_max_price", default_max_price)

            # Update request delay
            request_delay = self.request_delay_input.value()
            config_manager.update_setting("search.request_delay", request_delay)

            # Get the updated settings as a dictionary
            updated_settings = {
                "use_test_data": use_test_data,
                "use_playwright": use_playwright,
                "default_radius": default_radius,
                "default_max_price": default_max_price,
                "request_delay": request_delay,
                "playwright": {
                    "headless": self.headless_checkbox.isChecked(),
                    "screenshot_enabled": self.screenshot_checkbox.isChecked(),
                    "debug_mode": self.debug_checkbox.isChecked(),
                    "timeout": self.timeout_input.value(),
                    "slow_mo": slow_mo if slow_mo > 0 else None,
                },
            }

            # Emit signal with updated settings
            self.settings_saved.emit(updated_settings)

            logger.info("Saved search settings to config")
        except Exception as e:
            logger.error(f"Error saving search settings: {e}")

    def get_current_settings(self):
        """Get the current search settings.

        Returns:
            dict: Dictionary of current search settings
        """
        slow_mo = self.slow_mo_input.value()
        return {
            "use_test_data": self.use_test_data_checkbox.isChecked(),
            "use_playwright": self.use_playwright_checkbox.isChecked(),
            "default_radius": self.default_radius_input.value(),
            "default_max_price": self.default_max_price_input.value(),
            "request_delay": self.request_delay_input.value(),
            "playwright": {
                "headless": self.headless_checkbox.isChecked(),
                "screenshot_enabled": self.screenshot_checkbox.isChecked(),
                "debug_mode": self.debug_checkbox.isChecked(),
                "timeout": self.timeout_input.value(),
                "slow_mo": slow_mo if slow_mo > 0 else None,
            },
        }
