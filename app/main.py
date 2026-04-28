from dotenv import load_dotenv
from config import validate_config, ENV
from resilience import with_retry
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security.api_key import APIKeyHeader

import uuid
import os
from models import QueryRequest, QueryResponse
from providers import get_provider
from router import get_route
from governance import inspect as governance_inspect
from audit_logger import init_db, log_request, get_recent_logs

# -----------------------------
# App initialisation
# -----------------------------
app = FastAPI(
    title="AI Governance Gateway",
    description="Control plane between users and AI models",
    version="0.1.0"
)

@app.on_event("startup")
def startup():
    validate_config()
    init_db()
    print(f"Gateway started — ENV={ENV}")
    print(f"API key configured: {bool(GATEWAY_API_KEY)}")

# -----------------------------
# API Key authentication
# -----------------------------
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY")

def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if GATEWAY_API_KEY and api_key != GATEWAY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key"
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
# Audit endpoint
# -----------------------------
@app.get("/audit")
def audit(limit: int = 20, _ = Depends(verify_api_key)):
    return {"logs": get_recent_logs(limit=limit)}

# -----------------------------
# Query endpoint
# -----------------------------
@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, _ = Depends(verify_api_key)):
    request_id = str(uuid.uuid4())

    # Step 1 — Governance check
    gov = governance_inspect(request.prompt)
    if not gov["approved"]:
        log_request(
            request_id=request_id,
            prompt=request.prompt,
            outcome="blocked",
            metadata={
                "reason": gov["reason"],
                "pii_detected": gov["pii_detected"]
            }
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Request blocked by governance policy",
                "reason": gov["reason"],
                "request_id": request_id
            }
        )

    # Step 2 — Route
    safe_prompt = gov["masked_prompt"]
    route = get_route(safe_prompt)
    provider_name = route["provider"]

    try:
        provider = get_provider(provider_name)
        response_text = with_retry(provider.call, safe_prompt)

        log_request(
            request_id=request_id,
            prompt=safe_prompt,
            outcome="approved",
            metadata={
                "provider": provider_name,
                "classification": route["classification"],
                "pii_detected": gov["pii_detected"],
                "fallback_used": False
            }
        )

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
            response_text = with_retry(provider.call, safe_prompt)

            log_request(
                request_id=request_id,
                prompt=safe_prompt,
                outcome="approved",
                metadata={
                    "provider": fallback_name,
                    "classification": route["classification"],
                    "pii_detected": gov["pii_detected"],
                    "fallback_used": True
                }
            )

            return QueryResponse(
                response=response_text,
                model_used=fallback_name,
                policy_checked=True,
                request_id=request_id,
                classification=route["classification"],
                fallback_used=True
            )

        except Exception as fallback_error:
            log_request(
                request_id=request_id,
                prompt=safe_prompt,
                outcome="error",
                metadata={"error": str(fallback_error)}
            )
            import traceback
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail={
                    "error": str(fallback_error),
                    "request_id": request_id
                }
            )