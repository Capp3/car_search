"""Settings management using Pydantic for type safety and validation.

This module provides a centralized configuration system for the Car Search application,
handling environment variables, API keys, and application settings.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# Determine the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
ENV_FILE = CONFIG_DIR / ".env"

# Load environment variables from .env file if it exists
if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)


class LogSettings(BaseSettings):
    """Configuration settings for logging."""

    level: str = Field("INFO", description="Logging level")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    dir: Path = Field(PROJECT_ROOT / "logs", description="Directory for log files")
    file_name: str = Field("car_search.log", description="Default log file name")

    @field_validator("dir")
    @classmethod
    def create_log_dir(cls, v):
        """Create log directory if it doesn't exist."""
        os.makedirs(v, exist_ok=True)
        return v

    class Config:
        env_prefix = "LOG_"


class APISettings(BaseSettings):
    """Configuration settings for external APIs."""

    autotrader_base_url: str = Field("https://www.autotrader.co.uk", description="AutoTrader base URL")
    gemini_api_key: Optional[str] = Field(None, description="Google Gemini API key")
    car_data_api_key: Optional[str] = Field(None, description="Car data API key")
    edmunds_api_key: Optional[str] = Field(None, description="Edmunds API key")
    api_ninjas_key: Optional[str] = Field(None, description="API Ninjas API key")
    consumer_reports_key: Optional[str] = Field(None, description="Consumer Reports API key (RapidAPI)")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")

    class Config:
        env_prefix = "API_"


class UISettings(BaseSettings):
    """Configuration settings for the user interface."""

    theme: str = Field("system", description="UI theme (system, light, dark)")
    font_size: int = Field(12, description="UI font size")
    max_results_per_page: int = Field(20, description="Maximum search results per page")

    class Config:
        env_prefix = "UI_"


class SearchSettings(BaseSettings):
    """Configuration settings for car search functionality."""

    default_radius: int = Field(50, description="Default search radius in miles")
    default_max_price: int = Field(10000, description="Default maximum price")
    request_delay: float = Field(1.5, description="Delay between search requests in seconds")
    cache_expiry: int = Field(3600, description="Cache expiry time in seconds")
    use_test_data: bool = Field(False, description="Use test data when real data cannot be found")

    class Config:
        env_prefix = "SEARCH_"


class LLMSettings(BaseSettings):
    """Configuration settings for LLM functionality."""

    provider: str = Field("Google Gemini", description="Default LLM provider")
    gemini_model: str = Field("gemini-2.5-pro", description="Google Gemini model")
    openai_model: str = Field("gpt-4o", description="OpenAI model")
    anthropic_model: str = Field("claude-3-sonnet", description="Anthropic model")
    ollama_host: str = Field("http://localhost:11434", description="Ollama host URL")
    ollama_model: str = Field("llama3", description="Ollama model")
    temperature: float = Field(0.7, description="LLM temperature setting")
    max_tokens: int = Field(2048, description="Maximum tokens for LLM responses")

    class Config:
        env_prefix = "LLM_"


class AppSettings(BaseSettings):
    """Main application settings."""

    log: LogSettings = LogSettings()
    api: APISettings = APISettings()
    ui: UISettings = UISettings()
    search: SearchSettings = SearchSettings()
    llm: LLMSettings = LLMSettings()
    debug: bool = Field(False, description="Debug mode")

    class Config:
        env_file = ENV_FILE
        env_file_encoding = "utf-8"


# Create and export a singleton settings instance
settings = AppSettings()
