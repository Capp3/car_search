"""
Configuration settings for the Car Search application.

This module provides access to application settings from environment variables,
configuration files, and default values.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

# Base directory for the application
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Default configuration paths
CONFIG_DIR = BASE_DIR / "config"
USER_CONFIG_FILE = Path.home() / ".car_search" / "config.json"


class APISettings(BaseSettings):
    """Settings for external API integrations."""
    
    # Google Gemini API settings
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    
    # OpenAI API settings (optional)
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Anthropic API settings (optional)
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Car data API settings
    smartcar_api_key: Optional[str] = Field(None, env="SMARTCAR_API_KEY")
    edmunds_api_key: Optional[str] = Field(None, env="EDMUNDS_API_KEY")
    motorcheck_api_key: Optional[str] = Field(None, env="MOTORCHECK_API_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class LLMSettings(BaseSettings):
    """Settings for LLM integrations."""
    
    # Provider settings
    default_provider: str = "gemini"  # One of: gemini, openai, anthropic, ollama, mock
    
    # General LLM settings
    default_temperature: float = 0.7
    default_max_tokens: int = 1024
    
    # Model settings by provider
    gemini_model: str = "gemini-pro"
    openai_model: str = "gpt-3.5-turbo"
    anthropic_model: str = "claude-2"
    ollama_model: str = "llama2"
    
    # Request settings
    request_timeout: int = 30  # Timeout in seconds
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class AppSettings(BaseSettings):
    """General application settings."""
    
    # User preferences
    default_postcode: str = "BT7 3FN"  # Default from project brief
    default_radius: int = 50
    default_max_price: float = 2500.0
    
    # File storage settings
    cache_dir: Path = Path.home() / ".car_search" / "cache"
    data_dir: Path = Path.home() / ".car_search" / "data"
    
    # Web scraping settings
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    request_delay: float = 1.5  # Delay between requests in seconds
    
    # UI settings
    theme: str = "dark"  # One of: light, dark
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class Settings:
    """
    Main settings class that provides access to all application settings.
    
    This class loads settings from environment variables, configuration files,
    and default values. It also provides methods to update and save settings.
    """
    
    def __init__(self):
        self.api = APISettings()
        self.app = AppSettings()
        self.llm = LLMSettings()
        self._load_user_config()
        self._ensure_directories()
    
    def _load_user_config(self) -> None:
        """Load user configuration from the config file if it exists."""
        if USER_CONFIG_FILE.exists():
            try:
                with open(USER_CONFIG_FILE, "r") as f:
                    user_config = json.load(f)
                
                # Update API settings
                for key, value in user_config.get("api", {}).items():
                    if hasattr(self.api, key) and value:
                        setattr(self.api, key, value)
                
                # Update app settings
                for key, value in user_config.get("app", {}).items():
                    if hasattr(self.app, key) and value:
                        if key in ["cache_dir", "data_dir"]:
                            setattr(self.app, key, Path(value))
                        else:
                            setattr(self.app, key, value)
                
                # Update LLM settings
                for key, value in user_config.get("llm", {}).items():
                    if hasattr(self.llm, key) and value:
                        setattr(self.llm, key, value)
            
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading user config: {e}")
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        os.makedirs(self.app.cache_dir, exist_ok=True)
        os.makedirs(self.app.data_dir, exist_ok=True)
        os.makedirs(USER_CONFIG_FILE.parent, exist_ok=True)
    
    def save_user_config(self) -> None:
        """Save current settings to the user configuration file."""
        config = {
            "api": {
                "google_api_key": self.api.google_api_key,
                "openai_api_key": self.api.openai_api_key,
                "anthropic_api_key": self.api.anthropic_api_key,
                "smartcar_api_key": self.api.smartcar_api_key,
                "edmunds_api_key": self.api.edmunds_api_key,
                "motorcheck_api_key": self.api.motorcheck_api_key,
            },
            "app": {
                "default_postcode": self.app.default_postcode,
                "default_radius": self.app.default_radius,
                "default_max_price": self.app.default_max_price,
                "cache_dir": str(self.app.cache_dir),
                "data_dir": str(self.app.data_dir),
                "user_agent": self.app.user_agent,
                "request_delay": self.app.request_delay,
                "theme": self.app.theme,
            },
            "llm": {
                "default_provider": self.llm.default_provider,
                "default_temperature": self.llm.default_temperature,
                "default_max_tokens": self.llm.default_max_tokens,
                "gemini_model": self.llm.gemini_model,
                "openai_model": self.llm.openai_model,
                "anthropic_model": self.llm.anthropic_model,
                "ollama_model": self.llm.ollama_model,
                "request_timeout": self.llm.request_timeout,
                "max_retries": self.llm.max_retries,
            }
        }
        
        try:
            with open(USER_CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
        except IOError as e:
            print(f"Error saving user config: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for the specified provider."""
        if provider == "gemini":
            return self.api.google_api_key
        elif provider == "openai":
            return self.api.openai_api_key
        elif provider == "anthropic":
            return self.api.anthropic_api_key
        elif provider == "smartcar":
            return self.api.smartcar_api_key
        elif provider == "edmunds":
            return self.api.edmunds_api_key
        elif provider == "motorcheck":
            return self.api.motorcheck_api_key
        return None


# Create a singleton instance of the settings
settings = Settings()
