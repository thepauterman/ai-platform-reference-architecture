import os
import time
import vertexai
from vertexai.generative_models import GenerativeModel
from .base import BaseProvider


class VertexProvider(BaseProvider):
    """
    Google Vertex AI implementation of the provider interface.
    Uses Application Default Credentials - no API key needed.
    Gateway never calls this directly.
    """

    MODEL_NAME = "gemini-2.5-flash"

    def __init__(self):
        vertexai.init(
            project=os.getenv("GCP_PROJECT_ID"),
            location=os.getenv("GCP_REGION", "us-central1")
        )
        self.model = GenerativeModel(self.MODEL_NAME)

    def call(self, prompt: str) -> dict:
        t0 = time.perf_counter()
        response = self.model.generate_content(
            prompt,
            generation_config={"max_output_tokens": 500}
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        usage = response.usage_metadata
        tokens_used = (usage.prompt_token_count + usage.candidates_token_count) if usage else 0

        return {
            "text": response.text,
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "model_name": self.MODEL_NAME,
        }