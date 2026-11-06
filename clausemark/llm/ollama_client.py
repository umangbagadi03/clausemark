import requests

from clausemark import config
from clausemark.llm.errors import LLMError

# A local model on a laptop is much slower than a hosted one
OLLAMA_TIMEOUT_SECONDS = 300


class OllamaClient:
    def __init__(self):
        self.model = config.OLLAMA_MODEL
        self.name = "Ollama (" + self.model + ")"
        self.url = config.OLLAMA_URL + "/api/chat"

    def generate(self, system_prompt, user_prompt):
        body = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": 0.1},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            response = requests.post(self.url, json=body, timeout=OLLAMA_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.ConnectionError as error:
            raise LLMError(
                "Could not reach Ollama at " + config.OLLAMA_URL + ". "
                "Start it with `ollama serve`, or set an API key for another provider in .env."
            ) from error
        except requests.RequestException as error:
            raise LLMError("Ollama failed: " + type(error).__name__) from error

        return response.json()["message"]["content"]
