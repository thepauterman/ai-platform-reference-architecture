from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Every provider must implement the call() method.
    Gateway only interacts with this interface - never with providers directly.
    """

    @abstractmethod
    def call(self, prompt: str) -> dict:
        """
        Send a prompt to the model and return a result dict:
        {
            "text": str,         # response text
            "tokens_used": int,  # total tokens (input + output)
            "latency_ms": float, # wall-clock time for the API call
            "model_name": str,   # exact model identifier
        }
        """
        pass