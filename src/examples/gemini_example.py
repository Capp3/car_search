"""
Google Gemini Provider Example

This example demonstrates how to use the Google Gemini provider
with the LLM abstraction layer. It shows how to configure API keys,
create prompts, and generate responses.
"""

import asyncio
import os
import logging
from typing import Optional

from src.llm.provider import LLMProviderFactory, LLMPrompt, LLMProviderType
from src.config.settings import settings

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def run_example_with_key(api_key: Optional[str] = None):
    """
    Run an example using the Gemini provider with the specified API key.
    
    Args:
        api_key: The API key to use (if None, will try to use from settings)
    """
    # Create a provider factory
    factory = LLMProviderFactory()
    
    # Create a Gemini provider
    provider = factory.create_provider(
        provider_type=LLMProviderType.GEMINI,
        api_key=api_key,
        temperature=0.7,
        max_output_tokens=2048,
    )
    
    logger.info(f"Created provider: {provider.get_name()}")
    logger.info(f"Available models: {provider.get_models()}")
    logger.info(f"Using model: {provider.get_default_model()}")
    logger.info(f"Max tokens: {provider.get_max_tokens()}")
    
    # Create a prompt
    prompt = LLMPrompt(
        prompt="List 5 interesting facts about electric vehicles.",
        system_instructions="You are a helpful assistant that provides concise, accurate information.",
        temperature=0.7,
        max_tokens=1000,
    )
    
    try:
        # Generate a response
        logger.info("Generating response...")
        response = await provider.generate(prompt)
        
        # Print the response
        logger.info("\n--- Generated Response ---")
        logger.info(response.text)
        logger.info("--- End of Response ---\n")
        
        # Print token usage
        logger.info(f"Prompt tokens: {response.prompt_tokens}")
        logger.info(f"Completion tokens: {response.completion_tokens}")
        logger.info(f"Total tokens: {response.total_tokens}")
        
        return True
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return False


async def test_api_key_sources():
    """Test different API key sources."""
    logger.info("=== Testing API Key Sources ===")
    
    # 1. Try with explicit API key
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if api_key:
        logger.info("Testing with explicit API key...")
        success = await run_example_with_key(api_key)
        if success:
            logger.info("✅ Explicit API key works!")
        else:
            logger.error("❌ Explicit API key failed!")
    else:
        logger.warning("No explicit API key found in environment variables.")
    
    # 2. Try with environment variable (provider will pick it up automatically)
    if "GOOGLE_API_KEY" in os.environ:
        logger.info("Testing with API key from environment variables...")
        os.environ["PREVIOUS_KEY"] = os.environ["GOOGLE_API_KEY"]
        del os.environ["GOOGLE_API_KEY"]  # Temporarily remove to test settings
        
        # Instead we'll use settings
        settings.set_api_key("gemini", os.environ["PREVIOUS_KEY"])
        success = await run_example_with_key()
        
        # Restore environment variable
        os.environ["GOOGLE_API_KEY"] = os.environ["PREVIOUS_KEY"]
        del os.environ["PREVIOUS_KEY"]
        
        if success:
            logger.info("✅ API key from settings works!")
        else:
            logger.error("❌ API key from settings failed!")
    else:
        logger.warning("No API key found in environment variables to test settings method.")
    
    # 3. Try without any API key (should fall back to mock provider)
    if "GOOGLE_API_KEY" in os.environ:
        previous_key = os.environ["GOOGLE_API_KEY"]
        del os.environ["GOOGLE_API_KEY"]
    else:
        previous_key = None
    
    # Also clear from settings
    settings.set_api_key("gemini", None)
    
    logger.info("Testing without API key (should show warning but not crash)...")
    success = await run_example_with_key()
    
    # Restore API key if it existed
    if previous_key:
        os.environ["GOOGLE_API_KEY"] = previous_key
    
    if success:
        logger.info("✅ Provider handled missing API key correctly!")
    else:
        logger.info("ℹ️ Provider requires API key to function.")


async def main():
    """Run the main example."""
    logger.info("=== Google Gemini Provider Example ===")
    
    # Check if API key is available
    api_key = os.environ.get("GOOGLE_API_KEY") or settings.get_api_key("gemini")
    if not api_key:
        logger.warning("No Google API key found. The example will show how to handle missing keys.")
        logger.warning("To use Gemini, set GOOGLE_API_KEY environment variable or configure in settings.")
    
    # Run basic example
    await run_example_with_key()
    
    # Test different API key sources
    await test_api_key_sources()


if __name__ == "__main__":
    asyncio.run(main()) 