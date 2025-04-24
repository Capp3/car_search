"""
Google Gemini LLM provider implementation.

This module provides an implementation of the LLM provider interface
for Google's Gemini models using the Google Generative AI client.
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

# Maps from Gemini models to their context windows
MODEL_TOKEN_LIMITS = {
    "gemini-pro": 32000,
    "gemini-ultra": 32000,
    "gemini-pro-vision": 16000,
}

# Default model to use
DEFAULT_MODEL = "gemini-pro"

# Rate limiting settings
DEFAULT_RATE_LIMIT = {
    "requests_per_minute": 60,    # 60 requests per minute by default
    "tokens_per_minute": 200000,  # 200K tokens per minute by default
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


class GeminiProvider(LLMProvider):
    """
    Implementation of the LLM provider interface for Google Gemini.
    
    This provider uses the Google Generative AI API to interact with Gemini models.
    It requires an API key to be configured either in the application settings or
    through environment variables.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL, **kwargs):
        """
        Initialize the Gemini provider.
        
        Args:
            api_key: API key for Google Generative AI (if None, uses environment/settings)
            model: Model identifier to use
            **kwargs: Additional arguments to pass to the client
        """
        self.model = model
        
        # Get API key from environment, settings, or param
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or settings.get_api_key("gemini")
        
        if not self.api_key:
            logger.warning("No Google API key provided. The Gemini provider will not work without an API key.")
        
        # Initialize client as None - we'll create it on demand to avoid
        # immediate import errors if the package isn't installed
        self.client = None
        self.genai = None
        self.model_instance = None
        
        # Store additional kwargs for generation
        self.generation_config = {
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
            "max_output_tokens": kwargs.get("max_output_tokens", 1024),
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
        
        logger.info(f"Initialized Gemini provider with model: {model}")
    
    def _ensure_client(self):
        """
        Ensure the client is initialized.
        
        This method attempts to import and initialize the Google Generative AI client.
        It's called before any operation that requires the client.
        
        Raises:
            ImportError: If the required package isn't installed
            ValueError: If no API key is configured
        """
        if self.client is not None:
            return
        
        if not self.api_key:
            raise ValueError("Google API key is required for the Gemini provider")
        
        try:
            import google.generativeai as genai
            
            # Configure the client
            genai.configure(api_key=self.api_key)
            
            # Store the genai module so we can use it later
            self.genai = genai
            
            # Get the model
            self.model_instance = genai.GenerativeModel(self.model)
            
            # Set flag that client is configured
            self.client = True  
            
            logger.debug("Initialized Google Generative AI client")
        except ImportError:
            logger.error("Failed to import google.generativeai. "
                        "Please install it with: pip install google-generativeai")
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
                # Check if it's a rate limit error
                error_str = str(e).lower()
                is_rate_limit = any(msg in error_str for msg in 
                                    ["rate limit", "ratelimit", "quota", "too many requests", "429"])
                
                # If it's a rate limit error and we have retries left
                if is_rate_limit and retry_count < self.retry_limit:
                    retry_count += 1
                    logger.warning(f"Rate limit exceeded, retrying in {delay:.2f} seconds (attempt {retry_count}/{self.retry_limit})")
                    
                    # Wait with exponential backoff
                    await asyncio.sleep(delay)
                    
                    # Increase delay for next retry
                    delay = min(delay * self.retry_multiplier, self.max_retry_delay)
                else:
                    # Either not a rate limit error or out of retries
                    logger.error(f"Error calling Gemini API: {str(e)}")
                    raise
    
    async def generate(self, prompt: LLMPrompt) -> LLMResponse:
        """
        Generate text using Google Gemini.
        
        Args:
            prompt: The prompt to generate from
            
        Returns:
            The generated response
        """
        self._ensure_client()
        
        # Estimate token usage for rate limiting
        # A rough estimate: 1 token ≈ 4 characters for English text
        estimated_input_tokens = len(prompt.prompt) // 4
        if prompt.system_instructions:
            estimated_input_tokens += len(prompt.system_instructions) // 4
        
        # Wait if needed for rate limiting
        await self.rate_limiter.wait_if_needed(estimated_tokens=estimated_input_tokens)
        
        # Create generation configuration
        generation_config = self.genai.GenerationConfig(
            temperature=prompt.temperature or self.generation_config["temperature"],
            top_p=self.generation_config["top_p"],
            top_k=self.generation_config["top_k"],
            max_output_tokens=prompt.max_tokens or self.generation_config["max_output_tokens"],
        )
        
        # Set up safety settings (default - can be customized further)
        safety_settings = [
            {
                "category": self.genai.HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": self.genai.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            },
            {
                "category": self.genai.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": self.genai.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            },
            {
                "category": self.genai.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": self.genai.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            },
            {
                "category": self.genai.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": self.genai.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            }
        ]
        
        # Create the content as a list to handle system instructions
        content = []
        
        # Add system instructions if provided
        if prompt.system_instructions:
            content.append({"role": "system", "parts": [prompt.system_instructions]})
        
        # Add user prompt
        content.append({"role": "user", "parts": [prompt.prompt]})
        
        try:
            # Use rate limiting with retries
            start_time = time.time()
            
            if hasattr(self.model_instance, "generate_content_async"):
                # Use native async API with rate limiting
                async def generate_async():
                    return await self.model_instance.generate_content_async(
                        content=content,
                        generation_config=generation_config,
                        safety_settings=safety_settings,
                    )
                
                response = await self._handle_rate_limits(generate_async)
            else:
                # Fall back to synchronous API with executor and rate limiting
                async def generate_sync():
                    return await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.model_instance.generate_content(
                            content=content,
                            generation_config=generation_config,
                            safety_settings=safety_settings,
                        )
                    )
                
                response = await self._handle_rate_limits(generate_sync)
            
            # Calculate request time
            request_time = time.time() - start_time
            
            # Extract usage information
            prompt_tokens = getattr(response, "prompt_token_count", 0) 
            completion_tokens = getattr(response, "candidates_token_count", 0)
            
            if prompt_tokens == 0 and hasattr(response, "usage_metadata"):
                # Get from usage_metadata if available
                metadata = getattr(response, "usage_metadata", {})
                prompt_tokens = metadata.get("prompt_token_count", 0)
                completion_tokens = metadata.get("candidates_token_count", 0)
            
            # If we still don't have token counts, estimate them
            if prompt_tokens == 0:
                prompt_tokens = estimated_input_tokens
            
            if completion_tokens == 0:
                # Rough estimate for output tokens
                completion_tokens = len(str(response)) // 4
            
            # Record the API call for rate limiting
            total_tokens = prompt_tokens + completion_tokens
            self.rate_limiter.record_request(tokens_used=total_tokens)
            
            # Get the text from the response
            if hasattr(response, "text"):
                # Direct text property
                text = response.text
            elif hasattr(response, "candidates"):
                # From candidates
                candidates = response.candidates
                if candidates and len(candidates) > 0:
                    if hasattr(candidates[0], "content"):
                        content = candidates[0].content
                        if hasattr(content, "parts"):
                            text = "".join(str(part) for part in content.parts)
                        else:
                            text = str(content)
                    else:
                        text = str(candidates[0])
                else:
                    text = "No response generated."
            else:
                # Default fallback
                text = str(response)
                
            logger.info(f"Generated {completion_tokens} tokens with Gemini in {request_time:.2f}s")
            
            # Create and return the response
            return LLMResponse(
                text=text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                model=self.model,
                provider="gemini",
                metadata={
                    "raw_response": str(response),
                    "request_time": request_time,
                }
            )
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {str(e)}")
            raise
    
    def get_name(self) -> str:
        """Get the provider name."""
        return "Google Gemini"
    
    def get_models(self) -> List[str]:
        """Get available models."""
        if self.genai:
            try:
                models = self.genai.list_models()
                return [model.name for model in models if "gemini" in model.name]
            except:
                # Fallback to hardcoded models
                pass
        return list(MODEL_TOKEN_LIMITS.keys())
    
    def get_default_model(self) -> str:
        """Get the default model."""
        return self.model
    
    def get_max_tokens(self, model: Optional[str] = None) -> int:
        """Get the maximum tokens for the model."""
        model_name = model or self.model
        return MODEL_TOKEN_LIMITS.get(model_name, 32000)


# Register the provider with the factory
provider_factory.register_provider(LLMProviderType.GEMINI, GeminiProvider) 