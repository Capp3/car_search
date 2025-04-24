"""
LLM Provider Interface module.

This module defines the common interfaces for working with different LLM providers.
It implements an abstraction layer that allows seamless switching between
LLM providers like Google Gemini, OpenAI, Anthropic, and local models.
"""

import abc
import enum
import json
import logging
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, Type, Union, ClassVar

from src.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)


class LLMProviderType(enum.Enum):
    """Enum for supported LLM providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    MOCK = "mock"  # For testing purposes


@dataclass
class LLMPrompt:
    """
    Represents a prompt to be sent to an LLM.
    
    This class encapsulates all the information needed to create a prompt
    for an LLM, including the main prompt text, system instructions,
    and any additional context or parameters.
    """
    prompt: str
    system_instructions: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the prompt to a dictionary representation."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMPrompt":
        """Create a prompt from a dictionary representation."""
        return cls(**data)


@dataclass
class LLMResponse:
    """
    Represents a response from an LLM.
    
    This class encapsulates all the information returned from an LLM,
    including the generated text, usage information, and any additional
    metadata.
    """
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    provider: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the response to a dictionary representation."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMResponse":
        """Create a response from a dictionary representation."""
        return cls(**data)


class LLMProvider(abc.ABC):
    """
    Abstract base class for LLM providers.
    
    This class defines the common interface that all LLM providers must implement.
    It provides methods for generating text, completing prompts, and managing
    the LLM interaction.
    """
    
    @abc.abstractmethod
    async def generate(self, prompt: LLMPrompt) -> LLMResponse:
        """
        Generate text based on the given prompt.
        
        Args:
            prompt: The prompt to generate from
            
        Returns:
            The generated response
        """
        pass
    
    @abc.abstractmethod
    def get_name(self) -> str:
        """
        Get the name of the provider.
        
        Returns:
            Provider name
        """
        pass
    
    @abc.abstractmethod
    def get_models(self) -> List[str]:
        """
        Get the list of available models for this provider.
        
        Returns:
            List of model identifiers
        """
        pass
    
    @abc.abstractmethod
    def get_default_model(self) -> str:
        """
        Get the default model for this provider.
        
        Returns:
            Default model identifier
        """
        pass
    
    @abc.abstractmethod
    def get_max_tokens(self, model: Optional[str] = None) -> int:
        """
        Get the maximum number of tokens supported by the model.
        
        Args:
            model: Optional model identifier. If None, uses the default model.
            
        Returns:
            Maximum number of tokens
        """
        pass


class LLMProviderFactory:
    """
    Factory class for creating LLM provider instances.
    
    This class manages the creation of LLM provider instances based on
    configuration settings or explicit provider type specifications.
    """
    
    _providers: ClassVar[Dict[LLMProviderType, Type[LLMProvider]]] = {}
    
    @classmethod
    def register_provider(cls, provider_type: LLMProviderType, provider_class: Type[LLMProvider]) -> None:
        """
        Register a provider class for a specific provider type.
        
        Args:
            provider_type: The provider type to register
            provider_class: The provider class to register
        """
        cls._providers[provider_type] = provider_class
        logger.debug(f"Registered LLM provider {provider_type.value}: {provider_class.__name__}")
    
    @classmethod
    def create_provider(cls, provider_type: Union[LLMProviderType, str], **kwargs) -> LLMProvider:
        """
        Create a provider instance for the specified type.
        
        Args:
            provider_type: The provider type to create
            **kwargs: Additional arguments to pass to the provider constructor
            
        Returns:
            An instance of the specified provider
            
        Raises:
            ValueError: If the provider type is not registered
        """
        # Convert string to enum if needed
        if isinstance(provider_type, str):
            try:
                provider_type = LLMProviderType(provider_type.lower())
            except ValueError:
                valid_types = ", ".join(p.value for p in LLMProviderType)
                raise ValueError(f"Invalid provider type: {provider_type}. "
                                 f"Valid types are: {valid_types}")
        
        # Get the provider class
        provider_class = cls._providers.get(provider_type)
        if provider_class is None:
            valid_types = ", ".join(p.value for p in LLMProviderType)
            raise ValueError(f"No provider registered for type: {provider_type.value}. "
                             f"Valid types are: {valid_types}")
        
        # Create and return the provider instance
        return provider_class(**kwargs)
    
    @classmethod
    def get_default_provider(cls, **kwargs) -> LLMProvider:
        """
        Create the default provider based on configuration.
        
        Args:
            **kwargs: Additional arguments to pass to the provider constructor
            
        Returns:
            An instance of the default provider
        """
        # Get default provider type from settings
        default_type = getattr(settings.llm, "default_provider", "gemini")
        return cls.create_provider(default_type, **kwargs)
    
    @classmethod
    def initialize_providers(cls) -> None:
        """
        Initialize all provider classes.
        
        This method dynamically imports all provider implementations to ensure
        they are registered with the factory.
        """
        # Import available providers to trigger registration
        # These imports are placed here to avoid circular imports
        try:
            from .providers import gemini, openai, anthropic, ollama, mock  # noqa
            logger.info("LLM providers initialized successfully")
        except ImportError as e:
            logger.warning(f"Some LLM providers could not be initialized: {e}")


# Create a singleton instance for convenient access
provider_factory = LLMProviderFactory()

# Initialize providers during module import
# Comment out to defer initialization to when it's actually needed
# LLMProviderFactory.initialize_providers() 