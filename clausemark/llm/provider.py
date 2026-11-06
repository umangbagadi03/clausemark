from clausemark import config
from clausemark.llm.anthropic_client import AnthropicClient
from clausemark.llm.errors import LLMError
from clausemark.llm.gemini_client import GeminiClient
from clausemark.llm.ollama_client import OllamaClient
from clausemark.llm.openai_client import OpenAIClient

PROVIDERS = {
    "gemini": GeminiClient,
    "anthropic": AnthropicClient,
    "openai": OpenAIClient,
    "ollama": OllamaClient,
}


def pick_provider_name():
    # An explicit choice in .env always wins
    if config.LLM_PROVIDER:
        if config.LLM_PROVIDER not in PROVIDERS:
            raise ValueError(
                "Unknown LLM_PROVIDER '" + config.LLM_PROVIDER + "'. "
                "Use one of: gemini, anthropic, openai, ollama."
            )
        return config.LLM_PROVIDER

    # Otherwise use the first provider that has an API key.
    # Ollama runs locally and needs no key, so it is the fallback.
    if config.GEMINI_API_KEY:
        return "gemini"
    if config.ANTHROPIC_API_KEY:
        return "anthropic"
    if config.OPENAI_API_KEY:
        return "openai"
    return "ollama"


def check_key(provider_name):
    """A forced provider with no key should fail with a clear message, not deep inside an SDK."""
    keys = {
        "gemini": config.GEMINI_API_KEY,
        "anthropic": config.ANTHROPIC_API_KEY,
        "openai": config.OPENAI_API_KEY,
    }
    if provider_name in keys and not keys[provider_name]:
        raise LLMError("LLM_PROVIDER is " + provider_name + " but its API key is not set in .env.")


_llm = None


def get_llm():
    global _llm
    if _llm is None:
        provider_name = pick_provider_name()
        check_key(provider_name)
        client_class = PROVIDERS[provider_name]
        _llm = client_class()
    return _llm
