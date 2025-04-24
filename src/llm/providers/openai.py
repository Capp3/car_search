"""
OpenAI LLM provider implementation.

This module provides an implementation of the LLM provider interface
for OpenAI models using the OpenAI Python client.
"""

import logging
import os
import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from src.llm.provider import LLMProvider, LLMPrompt, LLMResponse, LLMProviderType, provider_factory
from src.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

# Maps from OpenAI models to their context windows
MODEL_TOKEN_LIMITS = {
    "gpt-3.5-turbo": 16385,
    "gpt-4": 8192,
    "gpt-4-turbo": 128000,
    "gpt-4-vision": 128000,
}

# Default model to use
DEFAULT_MODEL = "gpt-3.5-turbo"

# Rate limiting settings
DEFAULT_RATE_LIMIT = {
    "requests_per_minute": 50,    # 50 requests per minute by default
    "tokens_per_minute": 150000,  # 150K tokens per minute by default
    "retry_limit": 5,             # Maximum retries for rate limit errors
    "initial_retry_delay": 1.0,   # Initial retry delay in seconds
    "max_retry_delay": 60.0,      # Maximum retry delay in seconds
    "retry_multiplier": 2.0,      # Multiplier for exponential backoff
}


class RateLimiter:
    """
    Rate limiter for API requests.
    
    This class tracks request times and token usage to ensure rate limits
    are not exceeded.
    """
    
    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum number of requests per minute
            tokens_per_minute: Maximum number of tokens per minute
        """
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_times = []
        self.token_usage_times = []
        self.token_usage = []
    
    def _clean_history(self):
        """Clean up history older than one minute."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean request times
        self.request_times = [t for t in self.request_times if t > one_minute_ago]
        
        # Clean token usage
        recent_tokens = []
        recent_times = []
        for t, usage in zip(self.token_usage_times, self.token_usage):
            if t > one_minute_ago:
                recent_times.append(t)
                recent_tokens.append(usage)
        
        self.token_usage_times = recent_times
        self.token_usage = recent_tokens
    
    async def wait_if_needed(self, estimated_tokens: int = 0) -> float:
        """
        Wait if needed to stay within rate limits.
        
        Args:
            estimated_tokens: Estimated token usage for the next request
            
        Returns:
            Wait time in seconds (0 if no wait was needed)
        """
        self._clean_history()
        
        # Check request rate limit
        current_requests = len(self.request_times)
        wait_time = 0.0
        
        if current_requests >= self.requests_per_minute:
            # Calculate time until oldest request expires
            oldest_request = min(self.request_times)
            time_until_available = (oldest_request + timedelta(minutes=1) - datetime.now()).total_seconds()
            wait_time = max(wait_time, time_until_available)
        
        # Check token rate limit
        current_tokens = sum(self.token_usage)
        if current_tokens + estimated_tokens > self.tokens_per_minute:
            # Calculate time until oldest token usage expires
            if self.token_usage_times:
                oldest_token_time = min(self.token_usage_times)
                time_until_token_available = (oldest_token_time + timedelta(minutes=1) - datetime.now()).total_seconds()
                wait_time = max(wait_time, time_until_token_available)
        
        # Wait if needed
        if wait_time > 0:
            logger.info(f"Rate limit approaching, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
            # Recursively check again after waiting (in case multiple clients are making requests)
            return wait_time + await self.wait_if_needed(estimated_tokens)
        
        return 0.0
    
    def record_request(self, tokens_used: int = 0):
        """
        Record a request and its token usage.
        
        Args:
            tokens_used: Number of tokens used in the request
        """
        now = datetime.now()
        self.request_times.append(now)
        
        if tokens_used > 0:
            self.token_usage_times.append(now)
            self.token_usage.append(tokens_used)
            
        self._clean_history()


class OpenAIProvider(LLMProvider):
    """
    Implementation of the LLM provider interface for OpenAI.
    
    This provider uses the OpenAI API to interact with models like GPT-3.5 and GPT-4.
    It requires an API key to be configured either in the application settings or
    through environment variables.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL, **kwargs):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: API key for OpenAI (if None, uses environment/settings)
            model: Model identifier to use (default: gpt-3.5-turbo)
            **kwargs: Additional arguments to pass to the client
        """
        self.model = model
        
        # Get API key from environment, settings, or param
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or settings.get_api_key("openai")
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided. The OpenAI provider will not work without an API key.")
        
        # Initialize client as None - we'll create it on demand to avoid
        # immediate import errors if the package isn't installed
        self.client = None
        self.openai = None
        
        # Store additional kwargs for generation
        self.generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 1.0),
            "max_tokens": kwargs.get("max_tokens", 1024),
        }
        
        # Create rate limiter
        self.rate_limiter = RateLimiter(
            requests_per_minute=kwargs.get("requests_per_minute", DEFAULT_RATE_LIMIT["requests_per_minute"]),
            tokens_per_minute=kwargs.get("tokens_per_minute", DEFAULT_RATE_LIMIT["tokens_per_minute"])
        )
        
        # Set retry config
        self.retry_limit = kwargs.get("retry_limit", DEFAULT_RATE_LIMIT["retry_limit"])
        self.initial_retry_delay = kwargs.get("initial_retry_delay", DEFAULT_RATE_LIMIT["initial_retry_delay"])
        self.max_retry_delay = kwargs.get("max_retry_delay", DEFAULT_RATE_LIMIT["max_retry_delay"])
        self.retry_multiplier = kwargs.get("retry_multiplier", DEFAULT_RATE_LIMIT["retry_multiplier"])
        
        logger.info(f"Initialized OpenAI provider with model: {model}")
    
    def _ensure_client(self):
        """
        Ensure the client is initialized.
        
        This method attempts to import and initialize the OpenAI client.
        It's called before any operation that requires the client.
        
        Raises:
            ImportError: If the required package isn't installed
            ValueError: If no API key is configured
        """
        if self.client is not None:
            return
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required for the OpenAI provider")
        
        try:
            # Import OpenAI from separate imports to satisfy linter
            import openai
            # Import the OpenAI client class directly
            from openai import OpenAI
            
            # Store the openai module so we can use it later
            self.openai = openai
            
            # Create client instance
            self.client = OpenAI(api_key=self.api_key)
            
            logger.debug("Initialized OpenAI client")
        except ImportError:
            logger.error("Failed to import openai. "
                        "Please install it with: pip install openai")
            raise
    
    async def _handle_rate_limits(self, operation, *args, **kwargs):
        """
        Handle rate limits with retries and exponential backoff.
        
        Args:
            operation: Function to call
            args: Positional arguments to pass to the function
            kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If operation fails after all retries
        """
        retry_count = 0
        delay = self.initial_retry_delay
        
        while True:
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                # Check if this is a rate limit error
                is_rate_limit = False
                
                # Check for rate limit status code or message
                if hasattr(e, "status_code") and getattr(e, "status_code") == 429:
                    is_rate_limit = True
                elif str(e).lower().find("rate limit") != -1:
                    is_rate_limit = True
                
                # If it's not a rate limit error or we've exhausted retries, raise it
                if not is_rate_limit or retry_count >= self.retry_limit:
                    logger.error(f"Failed after {retry_count} retries: {str(e)}")
                    raise
                
                # Calculate backoff delay
                retry_count += 1
                wait_time = min(delay * (self.retry_multiplier ** (retry_count - 1)), self.max_retry_delay)
                
                logger.warning(f"Rate limit hit, retrying in {wait_time:.2f}s (retry {retry_count}/{self.retry_limit})")
                await asyncio.sleep(wait_time)
    
    async def generate(self, prompt: LLMPrompt) -> LLMResponse:
        """
        Generate text using the OpenAI API.
        
        Args:
            prompt: The prompt to generate from
            
        Returns:
            The generated response
            
        Raises:
            ImportError: If OpenAI package isn't installed
            ValueError: If the API key isn't configured
            Exception: For API errors
        """
        self._ensure_client()
        
        # Apply generation config from prompt
        temperature = prompt.temperature
        max_tokens = prompt.max_tokens
        
        # Prepare messages
        messages = []
        if prompt.system_instructions:
            messages.append({"role": "system", "content": prompt.system_instructions})
        
        messages.append({"role": "user", "content": prompt.prompt})
        
        # Estimate token count (very rough approximation)
        # In a production system, you'd use a proper tokenizer
        estimated_tokens = int(sum(len(msg["content"].split()) * 1.4 for msg in messages))
        
        # Wait if needed for rate limiting
        await self.rate_limiter.wait_if_needed(estimated_tokens)
        
        try:
            # Define sync generation function with client access ensured
            def _generate_sync(messages, temperature, max_tokens):
                if self.client is None:
                    raise ValueError("OpenAI client not initialized")
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            # Create an async wrapper for the synchronous API call
            async def generate_async():
                try:
                    response = await self._handle_rate_limits(
                        _generate_sync,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response
                except Exception as e:
                    logger.error(f"Error generating text with OpenAI: {str(e)}")
                    raise
            
            # Generate response
            start_time = time.time()
            response = await generate_async()
            elapsed_time = time.time() - start_time
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Get token counts
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Record request for rate limiting
            self.rate_limiter.record_request(total_tokens)
            
            # Create and return the response
            logger.info(f"Generated response with {completion_tokens} tokens in {elapsed_time:.2f}s")
            
            return LLMResponse(
                text=response_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model=self.model,
                provider="openai",
                metadata={
                    "generation_time": elapsed_time,
                    "finish_reason": response.choices[0].finish_reason
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to generate text with OpenAI: {str(e)}")
            raise
    
    def get_name(self) -> str:
        """Get the provider name."""
        return "OpenAI"
    
    def get_models(self) -> List[str]:
        """Get available models."""
        return list(MODEL_TOKEN_LIMITS.keys())
    
    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model or DEFAULT_MODEL
    
    def get_max_tokens(self, model: Optional[str] = None) -> int:
        """Get the maximum token limit for the specified model."""
        model_name = model or self.model or DEFAULT_MODEL
        return MODEL_TOKEN_LIMITS.get(model_name, 4096)


# Register the provider with the factory
provider_factory.register_provider(LLMProviderType.OPENAI, OpenAIProvider) 