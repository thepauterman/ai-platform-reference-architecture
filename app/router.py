import os
import logging
from policies import POLICIES

logger = logging.getLogger(__name__)

# -----------------------------
# Load from policies.yaml
# -----------------------------
_routing_config = POLICIES.get("routing", {})
_classification = _routing_config.get("classification", {})

APPROVED_PROVIDERS = _routing_config.get("approved_providers", ["openai", "anthropic", "vertex"])
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", _routing_config.get("default_provider", "openai"))
FALLBACK_PROVIDER = _routing_config.get("fallback_provider", "openai")

COMPLEXITY_KEYWORDS = _classification.get("complex", {}).get("trigger_keywords", [
    "analyse", "analyze", "compare", "summarise", "summarize",
    "explain in detail", "evaluate", "assess", "critique",
    "recommend", "strategy", "architecture", "design"
])

COMPLEX_PROVIDER = _classification.get("complex", {}).get("provider", "anthropic")
STANDARD_PROVIDER = _classification.get("standard", {}).get("provider", "openai")
SIMPLE_PROVIDER = _classification.get("simple", {}).get("provider", "vertex")


def classify_request(prompt: str) -> str:
    """
    Classify request complexity based on prompt content.
    Returns: "complex", "standard", or "simple"
    """
    prompt_lower = prompt.lower()

    if any(keyword in prompt_lower for keyword in COMPLEXITY_KEYWORDS):
        return "complex"
    elif len(prompt) > 200:
        return "standard"
    else:
        return "simple"


def select_provider(prompt: str) -> str:
    """
    Select the appropriate provider based on request classification.
    Rules loaded from policies.yaml.
    """
    classification = classify_request(prompt)

    if classification == "complex":
        return COMPLEX_PROVIDER
    elif classification == "standard":
        return STANDARD_PROVIDER
    else:
        return SIMPLE_PROVIDER


def get_route(prompt: str) -> dict:
    """
    Main routing function called by the gateway.
    Returns provider name and classification metadata.
    Validates against approved provider list.
    """
    provider = select_provider(prompt)

    if provider not in APPROVED_PROVIDERS:
        provider = DEFAULT_PROVIDER

    return {
        "provider": provider,
        "classification": classify_request(prompt),
        "fallback": FALLBACK_PROVIDER
    }