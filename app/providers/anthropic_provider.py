import os
import time
import anthropic
from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    """
    Anthropic implementation of the provider interface.
    Wraps the Anthropic SDK - gateway never calls this directly.
    """

    MODEL_NAME = "claude-sonnet-4-6"

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = self.MODEL_NAME

    def call(self, prompt: str) -> dict:
        t0 = time.perf_counter()
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
            timeout=10
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        return {
            "text": response.content[0].text,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "model_name": self.model,
        }