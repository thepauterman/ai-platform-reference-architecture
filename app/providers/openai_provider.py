import os
from openai import OpenAI
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """
    OpenAI implementation of the provider interface.
    Wraps the OpenAI SDK - gateway never calls this directly.
    """

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"

    def call(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            timeout=10
        )
        return response.choices[0].message.content