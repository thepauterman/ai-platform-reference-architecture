from governance import inspect as governance_inspect
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

    # Governance check — runs before routing
    gov = governance_inspect(request.prompt)
    if not gov["approved"]:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Request blocked by governance policy",
                "reason": gov["reason"],
                "request_id": request_id
            }
        )

    # Use masked prompt for routing and model call
    safe_prompt = gov["masked_prompt"]
    route = get_route(safe_prompt)
    provider_name = route["provider"]

    try:
        provider = get_provider(provider_name)
        response_text = provider.call(safe_prompt)
        return QueryResponse(
            response=response_text,
            model_used=provider_name,
            policy_checked=True,
            request_id=request_id,
            classification=route["classification"],
            fallback_used=False
        )
    except Exception as e:
        try:
            fallback_name = route["fallback"]
            provider = get_provider(fallback_name)
            response_text = provider.call(safe_prompt)
            return QueryResponse(
                response=response_text,
                model_used=fallback_name,
                policy_checked=True,
                request_id=request_id,
                classification=route["classification"],
                fallback_used=True
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