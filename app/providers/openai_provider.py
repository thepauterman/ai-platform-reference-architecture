import os
import time
from openai import OpenAI
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """
    OpenAI implementation of the provider interface.
    Wraps the OpenAI SDK - gateway never calls this directly.
    """

    MODEL_NAME = "gpt-4o-mini"

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = self.MODEL_NAME

    def call(self, prompt: str) -> dict:
        t0 = time.perf_counter()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            timeout=10
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        usage = response.usage
        tokens_used = (usage.prompt_tokens + usage.completion_tokens) if usage else 0

        return {
            "text": response.choices[0].message.content,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "model_name": self.model,
        }