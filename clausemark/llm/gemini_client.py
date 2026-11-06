import logging
import time

from google import genai
from google.genai import types

from clausemark import config
from clausemark.llm.errors import LLMError

logger = logging.getLogger(__name__)

# Free tier limits are per model, so try each model in turn
# and wait before going through the list again.
MAX_ROUNDS = 3
WAIT_SECONDS = 20


def is_temporary(error):
    if "timeout" in type(error).__name__.lower():
        return True

    text = str(error)
    for sign in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"):
        if sign in text:
            return True
    return False


class GeminiClient:
    def __init__(self):
        self.models = [config.GEMINI_MODEL] + config.GEMINI_FALLBACK_MODELS
        self.name = "Gemini (" + config.GEMINI_MODEL + ")"

        # The Gemini SDK takes its timeout in milliseconds
        http_options = types.HttpOptions(timeout=config.LLM_TIMEOUT_SECONDS * 1000)
        self.client = genai.Client(api_key=config.GEMINI_API_KEY, http_options=http_options)

    def call_model(self, model, system_prompt, user_prompt):
        settings = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1,
        )
        response = self.client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=settings,
        )
        return response.text or ""

    def generate(self, system_prompt, user_prompt):
        for round_number in range(1, MAX_ROUNDS + 1):
            for model in self.models:
                try:
                    reply = self.call_model(model, system_prompt, user_prompt)
                    self.name = "Gemini (" + model + ")"
                    return reply
                except Exception as error:
                    if not is_temporary(error):
                        logger.exception("Gemini call failed")
                        raise LLMError("Gemini failed: " + type(error).__name__) from error
                    logger.warning("%s is not available right now", model)

            if round_number < MAX_ROUNDS:
                logger.warning("Waiting %s seconds for Gemini", WAIT_SECONDS)
                time.sleep(WAIT_SECONDS)

        raise LLMError("Gemini is busy or out of quota. Try again in a minute.")
