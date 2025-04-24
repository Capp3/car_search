"""
Test module for OpenAI LLM provider.

This module contains tests for the OpenAI provider implementation.
"""

import unittest
import os
from unittest.mock import patch, MagicMock

import asyncio

from src.llm.provider import LLMPrompt, LLMProviderType, provider_factory
from src.llm.providers.openai import OpenAIProvider


class TestOpenAIProvider(unittest.TestCase):
    """Test case for OpenAI provider."""
    
    def setUp(self):
        """Set up test fixtures."""
        # No setup required for mock tests
        pass
        
    def _require_api_key(self):
        """Check if API key is available, skip test if not."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            self.skipTest("OPENAI_API_KEY environment variable not set")
        return api_key
    
    def test_provider_registration(self):
        """Test that the provider is properly registered."""
        # API key not needed for this test
        # Create provider via factory
        provider = provider_factory.create_provider(LLMProviderType.OPENAI)
        self.assertIsInstance(provider, OpenAIProvider)
        self.assertEqual(provider.get_name(), "OpenAI")
    
    def test_get_models(self):
        """Test getting available models."""
        api_key = self._require_api_key()
        provider = OpenAIProvider(api_key=api_key)
        models = provider.get_models()
        self.assertIsInstance(models, list)
        self.assertIn("gpt-3.5-turbo", models)
    
    def test_get_default_model(self):
        """Test getting default model."""
        api_key = self._require_api_key()
        provider = OpenAIProvider(api_key=api_key)
        default_model = provider.get_default_model()
        self.assertEqual(default_model, "gpt-3.5-turbo")
        
        # Test with custom model
        provider = OpenAIProvider(api_key=api_key, model="gpt-4")
        self.assertEqual(provider.get_default_model(), "gpt-4")
    
    def test_get_max_tokens(self):
        """Test getting max tokens."""
        api_key = self._require_api_key()
        provider = OpenAIProvider(api_key=api_key)
        max_tokens = provider.get_max_tokens()
        self.assertEqual(max_tokens, 16385)  # gpt-3.5-turbo
        
        # Test with specific model
        max_tokens = provider.get_max_tokens("gpt-4")
        self.assertEqual(max_tokens, 8192)
    
    @patch('openai.OpenAI')
    def test_generate_mocked(self, mock_openai):
        """Test generate method with mocked OpenAI client."""
        # Mock the OpenAI client - no API key needed
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, world!"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        # Set up the mock client to return our mock response
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create provider and prompt
        provider = OpenAIProvider(api_key="mock_key")
        prompt = LLMPrompt(
            prompt="Hello",
            system_instructions="You are a helpful assistant.",
            temperature=0.7,
            max_tokens=100
        )
        
        # Patch the _handle_rate_limits to bypass async handling
        original_handle_rate_limits = provider._handle_rate_limits
        
        async def mock_handle_rate_limits(operation, *args, **kwargs):
            # Just call the operation directly without await
            return operation(*args, **kwargs)
        
        # Apply the patch
        provider._handle_rate_limits = mock_handle_rate_limits
        
        try:
            # Call generate and check result
            response = asyncio.run(provider.generate(prompt))
            
            # Verify the response
            self.assertEqual(response.text, "Hello, world!")
            self.assertEqual(response.prompt_tokens, 10)
            self.assertEqual(response.completion_tokens, 5)
            self.assertEqual(response.total_tokens, 15)
            self.assertEqual(response.model, "gpt-3.5-turbo")
            self.assertEqual(response.provider, "openai")
            self.assertEqual(response.metadata["finish_reason"], "stop")
            
            # Verify the client was called with correct arguments
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args[1]
            self.assertEqual(call_args["model"], "gpt-3.5-turbo")
            self.assertEqual(call_args["temperature"], 0.7)
            self.assertEqual(call_args["max_tokens"], 100)
            self.assertEqual(len(call_args["messages"]), 2)
            self.assertEqual(call_args["messages"][0]["role"], "system")
            self.assertEqual(call_args["messages"][0]["content"], "You are a helpful assistant.")
            self.assertEqual(call_args["messages"][1]["role"], "user")
            self.assertEqual(call_args["messages"][1]["content"], "Hello")
        finally:
            # Restore the original method
            provider._handle_rate_limits = original_handle_rate_limits


if __name__ == '__main__':
    unittest.main() 