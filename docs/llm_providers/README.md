# LLM Providers Documentation

This directory contains documentation for the various LLM providers supported by the Car Search application.

## Available Providers

- [OpenAI](openai.md) - Integration with OpenAI's GPT models
- [Google Gemini](gemini.md) - Integration with Google's Gemini models
- [Mock Provider](mock.md) - Mock provider for testing without external API calls

## Provider Architecture

The LLM providers follow a common interface defined in `src/llm/provider.py`. This ensures that all providers can be used interchangeably and that the application can easily switch between different providers.

### Key Components

- **LLMProvider Interface**: Defines the common methods all providers must implement
- **LLMPrompt Class**: Represents a prompt to be sent to an LLM
- **LLMResponse Class**: Represents a response from an LLM
- **LLMProviderFactory**: Factory class for creating provider instances

## Adding a New Provider

To add a new LLM provider:

1. Create a new Python module in `src/llm/providers/`
2. Implement the `LLMProvider` interface
3. Register the provider with the factory
4. Add appropriate documentation in this directory

## Configuration

Provider configuration can be set in several ways:

1. Environment variables
2. Application settings
3. Direct parameters when creating the provider instance

See the individual provider documentation for specific configuration options. 