import re
import logging
from policies import POLICIES

logger = logging.getLogger(__name__)

# -----------------------------
# Load from policies.yaml
# -----------------------------
_pii_config = POLICIES.get("pii", {})
_input_config = POLICIES.get("input", {})
_unsafe_config = POLICIES.get("unsafe_content", {})

PII_PATTERNS = _pii_config.get("patterns", {
    "EMAIL": r'[\w\.-]+@[\w\.-]+\.\w{2,}',
    "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
    "PHONE": r'\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b',
    "CREDIT_CARD": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
})

BLOCKED_KEYWORDS = _unsafe_config.get("keywords", [
    "ignore previous instructions",
    "ignore all instructions",
    "jailbreak",
    "dan mode",
    "prompt injection",
    "disregard your instructions",
])

MIN_PROMPT_LENGTH = _input_config.get("min_length", 2)
MAX_PROMPT_LENGTH = _input_config.get("max_length", 4000)

PII_ACTION = _pii_config.get("action", "redact")
UNSAFE_ACTION = _unsafe_config.get("action", "block")


def validate_input(prompt: str) -> dict:
    """
    Validate prompt length.
    Returns: {"valid": bool, "reason": str}
    """
    if not prompt or len(prompt.strip()) < MIN_PROMPT_LENGTH:
        return {"valid": False, "reason": "Prompt too short"}
    if len(prompt) > MAX_PROMPT_LENGTH:
        return {"valid": False, "reason": f"Prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters"}
    return {"valid": True, "reason": None}


def detect_pii(prompt: str) -> list:
    """
    Detect PII entities in prompt.
    Returns list of detected PII types.
    """
    detected = []
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, prompt):
            detected.append(pii_type)
    return detected


def mask_pii(prompt: str) -> tuple[str, list]:
    """
    Mask PII in prompt with [REDACTED_TYPE] placeholders.
    Returns: (masked_prompt, list of detected PII types)
    """
    detected = []
    masked = prompt
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, masked):
            detected.append(pii_type)
            masked = re.sub(pattern, f"[REDACTED_{pii_type}]", masked)
    return masked, detected


def check_unsafe(prompt: str) -> dict:
    """
    Check for prompt injection and blocked keywords.
    Returns: {"safe": bool, "reason": str}
    """
    prompt_lower = prompt.lower()
    for keyword in BLOCKED_KEYWORDS:
        if keyword in prompt_lower:
            return {"safe": False, "reason": f"Blocked keyword detected: '{keyword}'"}
    return {"safe": True, "reason": None}


def inspect(prompt: str) -> dict:
    """
    Full governance inspection pipeline.
    Returns a governance result dict with all checks.
    Called by the gateway before routing.
    """
    # Step 1 — validate input
    validation = validate_input(prompt)
    if not validation["valid"]:
        return {
            "approved": False,
            "reason": validation["reason"],
            "masked_prompt": None,
            "pii_detected": [],
            "original_prompt": prompt,
        }

    # Step 2 — check for unsafe content
    safety = check_unsafe(prompt)
    if not safety["safe"]:
        return {
            "approved": False,
            "reason": safety["reason"],
            "masked_prompt": None,
            "pii_detected": [],
            "original_prompt": prompt,
        }

    # Step 3 — mask or block PII
    masked_prompt, pii_detected = mask_pii(prompt)
    if pii_detected and PII_ACTION == "block":
        return {
            "approved": False,
            "reason": f"PII detected and policy action is block: {pii_detected}",
            "masked_prompt": None,
            "pii_detected": pii_detected,
            "original_prompt": prompt,
        }

    return {
        "approved": True,
        "reason": None,
        "masked_prompt": masked_prompt,
        "pii_detected": pii_detected,
        "original_prompt": prompt,
    }