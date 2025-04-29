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

        layout.addWidget(behavior_group)

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

    def _load_settings(self):
        """Load current search settings from config."""
        try:
            # Load use_test_data setting
            use_test_data = config_manager.get_setting("search.use_test_data")
            self.use_test_data_checkbox.setChecked(bool(use_test_data))

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

            logger.debug("Loaded search settings from config")
        except Exception as e:
            logger.error(f"Error loading search settings: {e}")

    def _save_settings(self):
        """Save search settings to config."""
        try:
            # Update use_test_data setting
            use_test_data = self.use_test_data_checkbox.isChecked()
            config_manager.update_setting("search.use_test_data", use_test_data)

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
                "default_radius": default_radius,
                "default_max_price": default_max_price,
                "request_delay": request_delay,
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
        return {
            "use_test_data": self.use_test_data_checkbox.isChecked(),
            "default_radius": self.default_radius_input.value(),
            "default_max_price": self.default_max_price_input.value(),
            "request_delay": self.request_delay_input.value(),
        }
