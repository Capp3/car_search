#!/usr/bin/env python3
"""
Example script demonstrating the LLM provider abstraction layer.

This script shows how to:
1. Create an LLM prompt
2. Use the provider factory to get an LLM provider
3. Generate text using the provider
4. Process the response
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.llm import LLMPrompt, LLMResponse, provider_factory
from src.llm.provider import LLMProviderType

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def run_mock_example():
    """Run an example using the mock provider."""
    print("\n=== Mock Provider Example ===")
    
    # Create a provider using the factory
    provider = provider_factory.create_provider(LLMProviderType.MOCK)
    
    # Create a prompt
    prompt = LLMPrompt(
        prompt="I'm looking for a reliable car for daily commuting, with good fuel efficiency and under $15,000. What would you recommend?",
        system_instructions="You are a helpful assistant that specializes in car recommendations.",
        temperature=0.7,
        max_tokens=200
    )
    
    # Generate text
    response = await provider.generate(prompt)
    
    # Display the response
    print(f"\nPrompt: {prompt.prompt}")
    print(f"\nResponse from {provider.get_name()} ({response.model}):")
    print(f"{response.text}")
    print(f"\nToken usage: {response.total_tokens} tokens (Prompt: {response.prompt_tokens}, Completion: {response.completion_tokens})")


async def run_default_provider_example():
    """Run an example using the default provider."""
    print("\n=== Default Provider Example ===")
    
    # Get the default provider from settings
    provider = provider_factory.get_default_provider()
    print(f"Using default provider: {provider.get_name()}")
    
    # Create a prompt for car valuation
    prompt = LLMPrompt(
        prompt="I'm considering selling my 2018 Honda Accord with 50,000 miles. It's in excellent condition with no accidents. What would be a fair price to list it for?",
        system_instructions="You are a car valuation expert. Provide realistic price estimates based on the information given.",
        temperature=0.5
    )
    
    try:
        # Generate text
        response = await provider.generate(prompt)
        
        # Display the response
        print(f"\nPrompt: {prompt.prompt}")
        print(f"\nResponse from {provider.get_name()} ({response.model}):")
        print(f"{response.text}")
        print(f"\nToken usage: {response.total_tokens} tokens")
    except Exception as e:
        print(f"Error using default provider: {e}")
        print("Falling back to mock provider...")
        
        # Fallback to mock provider if default fails
        mock_provider = provider_factory.create_provider(LLMProviderType.MOCK)
        response = await mock_provider.generate(prompt)
        
        print(f"\nPrompt: {prompt.prompt}")
        print(f"\nResponse from {mock_provider.get_name()} (fallback):")
        print(f"{response.text}")


async def main():
    """Run the LLM examples."""
    print("LLM Provider Abstraction Layer Demo")
    print("===================================")
    
    print("\nAvailable providers:")
    # Initialize the providers
    provider_factory._providers.clear()  # Clear any existing providers for the demo
    from src.llm.providers import mock, gemini  # This registers the providers
    
    # Show available providers
    for provider_type in provider_factory._providers.keys():
        provider = provider_factory.create_provider(provider_type)
        print(f"- {provider.get_name()} (Type: {provider_type.value})")
        print(f"  Available models: {', '.join(provider.get_models())}")
        print(f"  Default model: {provider.get_default_model()}")
        print(f"  Max tokens: {provider.get_max_tokens()}")
        print()
    
    # Run examples
    await run_mock_example()
    await run_default_provider_example()
    
    print("\nLLM provider abstraction layer demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main()) 