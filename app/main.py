from dotenv import load_dotenv
load_dotenv()

import uuid
import os
from fastapi import FastAPI, HTTPException
from models import QueryRequest, QueryResponse
from providers import get_provider
from router import get_route

# -----------------------------
# App initialisation
# -----------------------------
app = FastAPI(
    title="AI Governance Gateway",
    description="Control plane between users and AI models",
    version="0.1.0"
)


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
    route = get_route(request.prompt)
    provider_name = route["provider"]

    try:
        provider = get_provider(provider_name)
        response_text = provider.call(request.prompt)
        return QueryResponse(
            response=response_text,
            model_used=provider_name,
            policy_checked=False,
            request_id=request_id,
            classification=route["classification"],
            fallback_used=False
        )
    except Exception as e:
        # Fallback to secondary provider
        try:
            fallback_name = route["fallback"]
            provider = get_provider(fallback_name)
            response_text = provider.call(request.prompt)
            return QueryResponse(
                response=response_text, 
                model_used=fallback_name,
                policy_checked=False,
                request_id=request_id,
                classification=route["classification"],
                fallback_used=True # ← tells you fallback was used
            )
        except Exception as fallback_error:
            import traceback
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail={
                    "error": str(fallback_error),
                    "request_id": request_id,
                    "provider": fallback_name
                }
            )

