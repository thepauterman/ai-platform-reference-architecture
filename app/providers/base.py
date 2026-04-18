from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Every provider must implement the call() method.
    Gateway only interacts with this interface - never with providers directly.
    """

    @abstractmethod
    def call(self, prompt: str) -> str:
        """
        Send a prompt to the model and return the response text.
        Each provider implements this differently internally.
        """
        pass