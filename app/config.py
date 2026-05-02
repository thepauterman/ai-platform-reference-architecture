import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# -----------------------------
# Environment
# -----------------------------
ENV = os.getenv("ENV", "dev")  # "dev" or "prod"

# -----------------------------
# Provider API keys
# -----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# -----------------------------
# Routing
# -----------------------------
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openai")

# -----------------------------
# GCP
# -----------------------------
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# -----------------------------
# Audit log
# -----------------------------
AUDIT_BACKEND = os.getenv("AUDIT_BACKEND", "sqlite")  # "sqlite" or "firestore"
AUDIT_DB_PATH = os.getenv("AUDIT_DB_PATH", "audit.db")  # sqlite only

# -----------------------------
# Config validation
# -----------------------------
REQUIRED_VARS = {
    "dev": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
    "prod": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GCP_PROJECT_ID"]
}

def validate_config():
    """
    Fail fast on startup if required env vars are missing.
    Called once in main.py startup event.
    """
    required = REQUIRED_VARS.get(ENV, [])
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables for ENV='{ENV}': {missing}"
        )
    logger.info(f"Config validated — ENV={ENV}")