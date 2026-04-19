import uuid
import os
from fastapi import FastAPI, HTTPException
from models import QueryRequest, QueryResponse
from providers import get_provider

# -----------------------------
# App initialisation
# -----------------------------
app = FastAPI(
    title="AI Governance Gateway",
    description="Control plane between users and AI models",
    version="0.1.0"
)

# Default provider — will become routing logic in Phase 6
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openai")

# -----------------------------
# Health check
# -----------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai-governance-gateway",
        "version": "0.1.0"
    }

# -----------------------------
# Query endpoint
# Phase 6: replace DEFAULT_PROVIDER with routing logic
# Phase 7: add policy + PII check before provider call
# Phase 8: add structured logging around this flow
# -----------------------------
@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    request_id = str(uuid.uuid4())

    try:
        provider = get_provider(DEFAULT_PROVIDER)
        response_text = provider.call(request.prompt)

        return QueryResponse(
            response=response_text,
            model_used=DEFAULT_PROVIDER,
            policy_checked=False,
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "request_id": request_id,
                "provider": DEFAULT_PROVIDER
            }
        )