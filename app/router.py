import os

# -----------------------------
# Approved model list
# Only providers in this list can be selected
# -----------------------------
APPROVED_PROVIDERS = ["openai", "anthropic", "vertex"]
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openai")
FALLBACK_PROVIDER = "openai"

# Keywords that signal a complex request
COMPLEXITY_KEYWORDS = [
    "analyse", "analyze", "compare", "summarise", "summarize",
    "explain in detail", "evaluate", "assess", "critique",
    "recommend", "strategy", "architecture", "design"
]

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
    Complex   → Anthropic (best reasoning)
    Standard  → OpenAI (balanced)
    Simple    → Vertex AI (cheapest)
    """
    classification = classify_request(prompt)

    if classification == "complex":
        return "anthropic"
    elif classification == "standard":
        return "openai"
    else:
        return "vertex"


def get_route(prompt: str) -> dict:
    """
    Main routing function called by the gateway.
    Returns provider name and classification metadata.
    Validates against approved provider list.
    """
    provider = select_provider(prompt)

    # Safety check — only approved providers allowed
    if provider not in APPROVED_PROVIDERS:
        provider = DEFAULT_PROVIDER

    return {
        "provider": provider,
        "classification": classify_request(prompt),
        "fallback": FALLBACK_PROVIDER
    }