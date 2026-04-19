from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .vertex_provider import VertexProvider


def get_provider(name: str):
    """
    Factory function — returns the correct provider instance by name.
    Gateway calls this instead of importing providers directly.
    Adding a new provider = add one file + one line here.
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "vertex": VertexProvider,
    }

    if name not in providers:
        raise ValueError(f"Unknown provider: {name}. Must be one of: {list(providers.keys())}")

    return providers[name]()