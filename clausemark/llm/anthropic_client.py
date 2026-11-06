import anthropic

from clausemark import config
from clausemark.llm.errors import LLMError


class AnthropicClient:
    def __init__(self):
        self.model = config.ANTHROPIC_MODEL
        self.name = "Claude (" + self.model + ")"
        self.client = anthropic.Anthropic(
            api_key=config.ANTHROPIC_API_KEY,
            timeout=config.LLM_TIMEOUT_SECONDS,
        )

    def generate(self, system_prompt, user_prompt):
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APIError as error:
            raise LLMError("Anthropic failed: " + type(error).__name__) from error

        if response.stop_reason == "refusal":
            raise LLMError("Claude declined to answer this request.")

        parts = []
        for block in response.content:
            if block.type == "text":
                parts.append(block.text)
        return "".join(parts)
