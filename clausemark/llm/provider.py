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

# A visitor can bring a key for these. Ollama runs on the visitor's own machine, so it cannot be used here.
VISITOR_PROVIDERS = ["gemini", "anthropic", "openai"]


def server_key(provider_name):
    keys = {
        "gemini": config.GEMINI_API_KEY,
        "anthropic": config.ANTHROPIC_API_KEY,
        "openai": config.OPENAI_API_KEY,
    }
    return keys.get(provider_name, "")


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


def server_has_model():
    """True when this server has its own model: a key in .env, or Ollama chosen on purpose.
    A public demo has neither, so it answers in search-only mode unless a visitor brings a key."""
    if config.LLM_PROVIDER == "ollama":
        return True
    if config.LLM_PROVIDER:
        return server_key(config.LLM_PROVIDER) != ""
    return pick_provider_name() != "ollama"


def make_client(provider_name, api_key):
    if provider_name not in PROVIDERS:
        raise LLMError("Unknown model provider: " + provider_name)
    if provider_name == "ollama":
        return OllamaClient()
    if not api_key:
        raise LLMError("No API key was given for " + provider_name + ".")
    return PROVIDERS[provider_name](api_key)


def check_key(provider_name):
    """A forced provider with no key should fail with a clear message, not deep inside an SDK."""
    if provider_name != "ollama" and not server_key(provider_name):
        raise LLMError("LLM_PROVIDER is " + provider_name + " but its API key is not set in .env.")


_llm = None


def get_llm():
    """The server's own model, made once and reused."""
    global _llm
    if _llm is None:
        provider_name = pick_provider_name()
        check_key(provider_name)
        _llm = make_client(provider_name, server_key(provider_name))
    return _llm
