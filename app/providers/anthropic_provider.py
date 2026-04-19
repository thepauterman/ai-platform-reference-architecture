import os
import anthropic
from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    """
    Anthropic implementation of the provider interface.
    Wraps the Anthropic SDK - gateway never calls this directly.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-6"

    def call(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
            timeout=10
        )
        return response.content[0].text