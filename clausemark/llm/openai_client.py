import openai

from clausemark import config
from clausemark.llm.errors import LLMError


class OpenAIClient:
    def __init__(self):
        self.model = config.OPENAI_MODEL
        self.name = "OpenAI (" + self.model + ")"
        self.client = openai.OpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=config.LLM_TIMEOUT_SECONDS,
        )

    def generate(self, system_prompt, user_prompt):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
        except openai.OpenAIError as error:
            raise LLMError("OpenAI failed: " + type(error).__name__) from error

        return response.choices[0].message.content or ""
