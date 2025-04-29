"""LLM configuration panel for the Car Search application.

This module provides a panel for configuring LLM provider settings.
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..config.manager import config_manager
from ..core.logging import get_logger

# Set up logger for this module
logger = get_logger(__name__)


class LLMConfigPanel(QWidget):
    """Panel for configuring LLM providers and settings."""

    # Signal emitted when config is saved
    config_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        """Initialize the LLM configuration panel."""
        super().__init__(parent)

        # Log initialization
        logger.info("Initializing LLM configuration panel")

        # Initialize UI components
        self._init_ui()

        # Load current configuration
        self._load_config()

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("LLM Configuration")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Provider selection
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("LLM Provider:"))

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Google Gemini", "OpenAI", "Anthropic", "Ollama"])
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)

        layout.addLayout(provider_layout)

        # Stacked widget for provider-specific settings
        self.settings_stack = QStackedWidget()
        layout.addWidget(self.settings_stack)

        # Add provider-specific setting panels
        self._add_gemini_settings()
        self._add_openai_settings()
        self._add_anthropic_settings()
        self._add_ollama_settings()

        # General LLM settings
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout(general_group)

        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.0, 1.0)
        self.temperature_input.setSingleStep(0.1)
        self.temperature_input.setValue(0.7)
        general_layout.addRow("Temperature:", self.temperature_input)

        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setRange(256, 8192)
        self.max_tokens_input.setSingleStep(256)
        self.max_tokens_input.setValue(2048)
        general_layout.addRow("Max Tokens:", self.max_tokens_input)

        layout.addWidget(general_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        button_layout.addWidget(self.test_button)

        self.save_button = QPushButton("Save Configuration")
        self.save_button.clicked.connect(self._save_config)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        # Spacer to push content to the top
        layout.addStretch(1)

    def _add_gemini_settings(self):
        """Add Google Gemini specific settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.gemini_api_key = QLineEdit()
        self.gemini_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_api_key.setPlaceholderText("Enter your Google Gemini API key")
        layout.addRow("API Key:", self.gemini_api_key)

        self.gemini_model = QComboBox()
        self.gemini_model.addItems(["gemini-2.5-pro", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"])
        layout.addRow("Model:", self.gemini_model)

        self.settings_stack.addWidget(widget)

    def _add_openai_settings(self):
        """Add OpenAI specific settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_api_key.setPlaceholderText("Enter your OpenAI API key")
        layout.addRow("API Key:", self.openai_api_key)

        self.openai_model = QComboBox()
        self.openai_model.addItems(["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        layout.addRow("Model:", self.openai_model)

        self.settings_stack.addWidget(widget)

    def _add_anthropic_settings(self):
        """Add Anthropic specific settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.anthropic_api_key = QLineEdit()
        self.anthropic_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_api_key.setPlaceholderText("Enter your Anthropic API key")
        layout.addRow("API Key:", self.anthropic_api_key)

        self.anthropic_model = QComboBox()
        self.anthropic_model.addItems(["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"])
        layout.addRow("Model:", self.anthropic_model)

        self.settings_stack.addWidget(widget)

    def _add_ollama_settings(self):
        """Add Ollama specific settings."""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.ollama_host = QLineEdit()
        self.ollama_host.setPlaceholderText("http://localhost:11434")
        self.ollama_host.setText("http://localhost:11434")
        layout.addRow("Host URL:", self.ollama_host)

        self.ollama_model = QLineEdit()
        self.ollama_model.setPlaceholderText("llama3")
        self.ollama_model.setText("llama3")
        layout.addRow("Model:", self.ollama_model)

        self.settings_stack.addWidget(widget)

    def _on_provider_changed(self, index):
        """Handle provider selection change.

        Args:
            index: Selected provider index
        """
        self.settings_stack.setCurrentIndex(index)
        logger.debug(f"Selected LLM provider: {self.provider_combo.currentText()}")

    def _load_config(self):
        """Load current LLM configuration from settings."""
        try:
            # Get LLM provider
            provider = config_manager.get_setting("llm.provider")
            if provider:
                index = self.provider_combo.findText(provider)
                if index >= 0:
                    self.provider_combo.setCurrentIndex(index)

            # Get API keys
            gemini_key = config_manager.get_setting("api.gemini_api_key")
            if gemini_key:
                self.gemini_api_key.setText(gemini_key)

            openai_key = config_manager.get_setting("api.openai_api_key")
            if openai_key:
                self.openai_api_key.setText(openai_key)

            anthropic_key = config_manager.get_setting("api.anthropic_api_key")
            if anthropic_key:
                self.anthropic_api_key.setText(anthropic_key)

            # Get models
            gemini_model = config_manager.get_setting("llm.gemini_model")
            if gemini_model:
                index = self.gemini_model.findText(gemini_model)
                if index >= 0:
                    self.gemini_model.setCurrentIndex(index)

            openai_model = config_manager.get_setting("llm.openai_model")
            if openai_model:
                index = self.openai_model.findText(openai_model)
                if index >= 0:
                    self.openai_model.setCurrentIndex(index)

            anthropic_model = config_manager.get_setting("llm.anthropic_model")
            if anthropic_model:
                index = self.anthropic_model.findText(anthropic_model)
                if index >= 0:
                    self.anthropic_model.setCurrentIndex(index)

            # Get Ollama settings
            ollama_host = config_manager.get_setting("llm.ollama_host")
            if ollama_host:
                self.ollama_host.setText(ollama_host)

            ollama_model = config_manager.get_setting("llm.ollama_model")
            if ollama_model:
                self.ollama_model.setText(ollama_model)

            # Get general settings
            temperature = config_manager.get_setting("llm.temperature")
            if temperature is not None:
                self.temperature_input.setValue(temperature)

            max_tokens = config_manager.get_setting("llm.max_tokens")
            if max_tokens:
                self.max_tokens_input.setValue(max_tokens)

            logger.info("Loaded LLM configuration from settings")

        except Exception as e:
            logger.error(f"Error loading LLM configuration: {e}")

    def _save_config(self):
        """Save the current LLM configuration to settings."""
        try:
            # Get current provider
            provider = self.provider_combo.currentText()
            config_manager.update_setting("llm.provider", provider)

            # Save API keys
            config_manager.update_setting("api.gemini_api_key", self.gemini_api_key.text())
            config_manager.update_setting("api.openai_api_key", self.openai_api_key.text())
            config_manager.update_setting("api.anthropic_api_key", self.anthropic_api_key.text())

            # Save models
            config_manager.update_setting("llm.gemini_model", self.gemini_model.currentText())
            config_manager.update_setting("llm.openai_model", self.openai_model.currentText())
            config_manager.update_setting("llm.anthropic_model", self.anthropic_model.currentText())

            # Save Ollama settings
            config_manager.update_setting("llm.ollama_host", self.ollama_host.text())
            config_manager.update_setting("llm.ollama_model", self.ollama_model.text())

            # Save general settings
            config_manager.update_setting("llm.temperature", self.temperature_input.value())
            config_manager.update_setting("llm.max_tokens", self.max_tokens_input.value())

            logger.info(f"Saved LLM configuration with provider: {provider}")

            # Emit config saved signal with config data
            config_data = {
                "provider": provider,
                "model": self._get_current_model(),
                "temperature": self.temperature_input.value(),
                "max_tokens": self.max_tokens_input.value(),
            }
            self.config_saved.emit(config_data)

        except Exception as e:
            logger.error(f"Error saving LLM configuration: {e}")

    def _test_connection(self):
        """Test the connection to the current LLM provider."""
        provider = self.provider_combo.currentText()
        model = self._get_current_model()

        # TODO: Implement actual connection test with selected provider
        # For now, just log the attempt
        logger.info(f"Testing connection to {provider} with model {model}")

        # This would be implemented with the LLM service once available

    def _get_current_model(self):
        """Get the currently selected model based on provider."""
        provider_index = self.provider_combo.currentIndex()

        if provider_index == 0:  # Google Gemini
            return self.gemini_model.currentText()
        elif provider_index == 1:  # OpenAI
            return self.openai_model.currentText()
        elif provider_index == 2:  # Anthropic
            return self.anthropic_model.currentText()
        elif provider_index == 3:  # Ollama
            return self.ollama_model.text()

        return ""

    def get_current_config(self):
        """Get the current LLM configuration.

        Returns:
            dict: Current LLM configuration
        """
        provider = self.provider_combo.currentText()

        config = {
            "provider": provider,
            "model": self._get_current_model(),
            "temperature": self.temperature_input.value(),
            "max_tokens": self.max_tokens_input.value(),
        }

        # Add provider-specific settings
        if provider == "Google Gemini":
            config["api_key"] = self.gemini_api_key.text()
        elif provider == "OpenAI":
            config["api_key"] = self.openai_api_key.text()
        elif provider == "Anthropic":
            config["api_key"] = self.anthropic_api_key.text()
        elif provider == "Ollama":
            config["host"] = self.ollama_host.text()

        return config
