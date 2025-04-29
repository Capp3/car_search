"""Application module for the Car Search application.

This module provides functionality to set up and launch the Qt application.
"""

import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from ..config.manager import config_manager
from ..core.logging import get_logger
from .main_window import MainWindow

# Set up logger for this module
logger = get_logger(__name__)


def run_application():
    """Initialize and run the Qt application.

    Returns:
        int: Application exit code
    """
    logger.info("Starting Car Search Qt application")

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Car Search")

    # Apply font size from configuration
    font_size = config_manager.get_setting("ui.font_size")
    font = QFont()
    font.setPointSize(font_size)
    app.setFont(font)

    # Apply theme if specified
    theme = config_manager.get_setting("ui.theme")
    if theme and theme != "system":
        try:
            if theme == "dark":
                _apply_dark_theme(app)
            # Could add more themes here
        except Exception as e:
            logger.warning(f"Failed to apply {theme} theme: {e}")

    # Create and show main window
    main_window = MainWindow()

    # Run application
    exit_code = app.exec()

    logger.info(f"Application closed with exit code: {exit_code}")
    return exit_code


def _apply_dark_theme(app):
    """Apply dark theme to the application.

    Args:
        app: QApplication instance
    """
    # Simple dark theme stylesheet
    app.setStyleSheet("""
        QWidget {
            background-color: #2D2D30;
            color: #CCCCCC;
        }
        QMainWindow, QDialog {
            background-color: #1E1E1E;
        }
        QLineEdit, QComboBox, QSpinBox {
            background-color: #333337;
            border: 1px solid #555555;
            color: #CCCCCC;
            padding: 2px;
        }
        QPushButton {
            background-color: #0E639C;
            color: white;
            border: 1px solid #0E639C;
            padding: 4px 8px;
        }
        QPushButton:hover {
            background-color: #1177BB;
        }
        QTabWidget::pane {
            border: 1px solid #3F3F46;
        }
        QTabBar::tab {
            background-color: #252526;
            color: #CCCCCC;
            padding: 6px 12px;
        }
        QTabBar::tab:selected {
            background-color: #3F3F46;
        }
        QGroupBox {
            border: 1px solid #3F3F46;
            margin-top: 6px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
    """)
