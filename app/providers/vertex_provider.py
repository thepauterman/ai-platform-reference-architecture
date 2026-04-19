import os
import vertexai
from vertexai.generative_models import GenerativeModel
from .base import BaseProvider


class VertexProvider(BaseProvider):
    """
    Google Vertex AI implementation of the provider interface.
    Uses Application Default Credentials - no API key needed.
    Gateway never calls this directly.
    """

    def __init__(self):
        vertexai.init(
            project=os.getenv("GCP_PROJECT_ID"),
            location=os.getenv("GCP_REGION", "us-central1")
        )
        self.model = GenerativeModel("gemini-1.5-flash")

    def call(self, prompt: str) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config={"max_output_tokens": 500}
        )
        return response.text