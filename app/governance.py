import re
import time
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
    Returns a governance result dict with all checks and per-step timing.
    Called by the gateway before routing.
    """
    pipeline_steps = []

    # Step 1 — validate input
    t0 = time.perf_counter()
    validation = validate_input(prompt)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    if not validation["valid"]:
        pipeline_steps.append({
            "step": "INPUT_VALIDATION",
            "status": "FAIL",
            "detail": validation["reason"],
            "latency_ms": elapsed,
        })
        return {
            "approved": False,
            "reason": validation["reason"],
            "masked_prompt": None,
            "pii_detected": [],
            "original_prompt": prompt,
            "pipeline_steps": pipeline_steps,
        }

    pipeline_steps.append({
        "step": "INPUT_VALIDATION",
        "status": "PASS",
        "detail": "OK",
        "latency_ms": elapsed,
    })

    # Step 2 — check for unsafe content
    t0 = time.perf_counter()
    safety = check_unsafe(prompt)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    if not safety["safe"]:
        pipeline_steps.append({
            "step": "SAFETY_CHECK",
            "status": "FAIL",
            "detail": safety["reason"],
            "latency_ms": elapsed,
        })
        return {
            "approved": False,
            "reason": safety["reason"],
            "masked_prompt": None,
            "pii_detected": [],
            "original_prompt": prompt,
            "pipeline_steps": pipeline_steps,
        }

    pipeline_steps.append({
        "step": "SAFETY_CHECK",
        "status": "PASS",
        "detail": "OK",
        "latency_ms": elapsed,
    })

    # Step 3 — mask or block PII
    t0 = time.perf_counter()
    masked_prompt, pii_detected = mask_pii(prompt)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    pii_count = len(pii_detected)
    pii_detail = f"{pii_count} types detected" if pii_count else "no PII"

    if pii_detected and PII_ACTION == "block":
        pipeline_steps.append({
            "step": "PII_DETECTION",
            "status": "BLOCKED",
            "detail": f"{pii_detail} — policy: block",
            "latency_ms": elapsed,
        })
        return {
            "approved": False,
            "reason": f"PII detected and policy action is block: {pii_detected}",
            "masked_prompt": None,
            "pii_detected": pii_detected,
            "original_prompt": prompt,
            "pipeline_steps": pipeline_steps,
        }

    pipeline_steps.append({
        "step": "PII_DETECTION",
        "status": "PASS",
        "detail": pii_detail,
        "latency_ms": elapsed,
    })

    return {
        "approved": True,
        "reason": None,
        "masked_prompt": masked_prompt,
        "pii_detected": pii_detected,
        "original_prompt": prompt,
        "pipeline_steps": pipeline_steps,
    }