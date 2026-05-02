import yaml
import os
import logging

logger = logging.getLogger(__name__)

POLICIES_PATH = os.getenv("POLICIES_PATH", "policies.yaml")

def load_policies() -> dict:
    """
    Load governance policies from YAML config file.
    Called once at module import time.
    """
    try:
        with open(POLICIES_PATH) as f:
            policies = yaml.safe_load(f)
            logger.info(f"Policies loaded from {POLICIES_PATH}")
            return policies
    except FileNotFoundError:
        logger.warning(f"policies.yaml not found at {POLICIES_PATH} — using defaults")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse policies.yaml: {e}")
        raise RuntimeError(f"Invalid policies.yaml: {e}")

POLICIES = load_policies()