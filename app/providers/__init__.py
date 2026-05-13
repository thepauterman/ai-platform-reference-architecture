from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .vertex_provider import VertexProvider


PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "vertex": VertexProvider,
}

PROVIDER_MODELS = {name: cls.MODEL_NAME for name, cls in PROVIDER_CLASSES.items()}


def get_provider(name: str):
    """
    Factory function — returns the correct provider instance by name.
    Gateway calls this instead of importing providers directly.
    Adding a new provider = add one file + one line here.
    """
    if name not in PROVIDER_CLASSES:
        raise ValueError(f"Unknown provider: {name}. Must be one of: {list(PROVIDER_CLASSES.keys())}")

    return PROVIDER_CLASSES[name]()