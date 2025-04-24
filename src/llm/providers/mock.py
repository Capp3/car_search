"""
Mock LLM provider implementation for testing purposes.

This module provides a mock implementation of the LLM provider interface
that returns predefined responses for testing without external API calls.
"""

import logging
import random
from typing import Dict, List, Optional, Any

from src.llm.provider import LLMProvider, LLMPrompt, LLMResponse, LLMProviderType, provider_factory

# Configure logging
logger = logging.getLogger(__name__)

# Sample car-related responses for the mock provider
MOCK_RESPONSES = [
    "Based on your requirements, I recommend the Toyota Camry. It's reliable, fuel-efficient, and has excellent safety ratings.",
    "The Honda Accord would be a great choice for you. It offers a good balance of comfort, efficiency, and features.",
    "Consider the Mazda CX-5 if you need more space. It combines practicality with an engaging driving experience.",
    "For your budget, a certified pre-owned Lexus ES would provide luxury features at a reasonable price point.",
    "A Subaru Outback might be perfect for your needs, especially if you need all-wheel drive for various weather conditions.",
]


class MockLLMProvider(LLMProvider):
    """
    Mock implementation of the LLM provider interface.
    
    This provider returns predefined responses for testing without making
    actual API calls to external services.
    """
    
    def __init__(self, model: str = "mock-model-v1", **kwargs):
        """
        Initialize the mock provider.
        
        Args:
            model: Model identifier to simulate
            **kwargs: Additional arguments (ignored)
        """
        self.model = model
        logger.info(f"Initialized mock LLM provider with model: {model}")
    
    async def generate(self, prompt: LLMPrompt) -> LLMResponse:
        """
        Generate a mock response.
        
        Args:
            prompt: The prompt (used for token counting only)
            
        Returns:
            A mock response with a predefined text
        """
        # Simulate processing time and randomness
        prompt_text = prompt.prompt
        prompt_tokens = len(prompt_text.split())
        
        # Select a random response
        response_text = random.choice(MOCK_RESPONSES)
        completion_tokens = len(response_text.split())
        
        logger.info(f"Mock LLM generated response with {completion_tokens} tokens")
        
        return LLMResponse(
            text=response_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=self.model,
            provider="mock",
            metadata={"mock": True}
        )
    
    def get_name(self) -> str:
        """Get the provider name."""
        return "Mock Provider"
    
    def get_models(self) -> List[str]:
        """Get available models."""
        return ["mock-model-v1", "mock-model-v2"]
    
    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model
    
    def get_max_tokens(self, model: Optional[str] = None) -> int:
        """Get the maximum tokens for the model."""
        return 4096  # Simulate a typical token limit


# Register the provider with the factory
provider_factory.register_provider(LLMProviderType.MOCK, MockLLMProvider) 