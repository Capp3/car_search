# OpenAI Provider Integration

This document outlines the implementation of the OpenAI provider for the Car Search application.

## Overview

The OpenAI provider allows the application to use OpenAI's GPT models (like GPT-3.5 and GPT-4) through a consistent interface that matches the application's LLM abstraction layer.

## Features

- Support for different OpenAI models (GPT-3.5-Turbo, GPT-4, etc.)
- Asynchronous API calls
- Rate limiting to prevent API quota issues
- Error handling with exponential backoff
- Token usage tracking

## Configuration

### API Keys

To use the OpenAI provider, you need to set up an API key:

1. Obtain an API key from [OpenAI's platform](https://platform.openai.com/)
2. Add it to your `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. Alternatively, set it as an environment variable or configure it in the application settings

### Available Models

The following models are supported:

| Model          | Token Limit | Description                                     |
|----------------|-------------|-------------------------------------------------|
| gpt-3.5-turbo  | 16,385      | Balanced model for most general tasks           |
| gpt-4          | 8,192       | More capable model with higher reasoning        |
| gpt-4-turbo    | 128,000     | Latest GPT-4 with larger context window         |
| gpt-4-vision   | 128,000     | Vision-capable model that can process images    |

## Usage

### Using the Factory

```python
from src.llm.provider import LLMPrompt, LLMProviderType, provider_factory

# Create the provider
provider = provider_factory.create_provider(LLMProviderType.OPENAI)

# Create a prompt
prompt = LLMPrompt(
    prompt="Recommend a car for a family of 4 with good safety ratings and fuel efficiency.",
    system_instructions="You are a helpful car advisor. Provide concise, accurate recommendations.",
    temperature=0.7,
    max_tokens=400
)

# Generate a response
response = await provider.generate(prompt)
print(response.text)
```

### Direct Initialization

```python
from src.llm.providers.openai import OpenAIProvider
from src.llm.provider import LLMPrompt

# Create provider with specific model
provider = OpenAIProvider(model="gpt-4")

# Create and send prompt
prompt = LLMPrompt(prompt="What are the key features to look for in a reliable used car?")
response = await provider.generate(prompt)
```

## Rate Limiting

The OpenAI provider includes built-in rate limiting to prevent exceeding API quotas:

- Default: 50 requests per minute
- Token limit: 150,000 tokens per minute
- Configurable via constructor parameters

## Implementation Details

The provider implements the `LLMProvider` interface and handles:

- Client initialization with proper error handling
- Message formatting for chat completions
- Token counting and usage tracking
- Response parsing and formatting

## Testing

Unit tests are available in `tests/test_openai_provider.py` and include tests for:

- Provider registration
- Model listing and configuration
- Mock API response handling
- Error scenarios

## Dependencies

- `openai`: The official OpenAI Python client
- Install with: `pip install openai` or `poetry add openai` 