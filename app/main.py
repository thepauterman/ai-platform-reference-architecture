from dotenv import load_dotenv
from config import validate_config, ENV
from resilience import with_retry
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import time
import uuid
import os
import traceback
import logging

from models import QueryRequest, QueryResponse
from providers import get_provider
from router import get_route
from governance import inspect as governance_inspect
from audit_logger import init_db, log_request, get_recent_logs, get_log_by_request_id
from metrics import compute_metrics

logger = logging.getLogger(__name__)

# -----------------------------
# API Key authentication
# -----------------------------
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY")

# -----------------------------
# App initialisation
# -----------------------------
app = FastAPI(
    title="AI Governance Gateway",
    description="Control plane between users and AI models",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    validate_config()
    init_db()
    logger.info(f"Gateway started — ENV={ENV}")
    logger.info(f"API key configured: {bool(GATEWAY_API_KEY)}")

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
# Audit endpoints
# -----------------------------
@app.get("/audit")
def audit(limit: int = 20, _ = Depends(verify_api_key)):
    return {"logs": get_recent_logs(limit=limit)}

@app.get("/audit/{request_id}")
def audit_detail(request_id: str, _ = Depends(verify_api_key)):
    entry = get_log_by_request_id(request_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Request not found")
    return entry

# -----------------------------
# Metrics endpoint
# -----------------------------
@app.get("/metrics")
def metrics(_ = Depends(verify_api_key)):
    return compute_metrics()

# -----------------------------
# Query endpoint
# -----------------------------
@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, _ = Depends(verify_api_key)):
    request_id = str(uuid.uuid4())
    pipeline_trace = []

    # Step 1 — Client request received
    t_start = time.perf_counter()
    pipeline_trace.append({
        "step": "CLIENT_REQUEST",
        "status": "OK",
        "detail": "received",
        "latency_ms": 0,
    })

    # Step 2 — Governance check
    gov = governance_inspect(request.prompt)
    gov_steps = gov.get("pipeline_steps", [])
    pipeline_trace.extend(gov_steps)

    if not gov["approved"]:
        # Add policy check as failed
        pipeline_trace.append({
            "step": "POLICY_CHECK",
            "status": "BLOCKED",
            "detail": gov["reason"],
            "latency_ms": 0,
        })
        total_ms = round((time.perf_counter() - t_start) * 1000, 1)

        log_request(
            request_id=request_id,
            prompt=request.prompt,
            outcome="blocked",
            metadata={
                "reason": gov["reason"],
                "pii_detected": gov["pii_detected"],
                "pipeline_trace": pipeline_trace,
                "total_latency_ms": total_ms,
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

    pipeline_trace.append({
        "step": "POLICY_CHECK",
        "status": "PASS",
        "detail": "all checks passed",
        "latency_ms": 0,
    })

    # Step 3 — Route
    safe_prompt = gov["masked_prompt"]
    t_route = time.perf_counter()
    route = get_route(safe_prompt)
    route_ms = round((time.perf_counter() - t_route) * 1000, 1)
    provider_name = route["provider"]

    pipeline_trace.append({
        "step": "ROUTING_DECISION",
        "status": "OK",
        "detail": f"{provider_name} ({route['classification']})",
        "latency_ms": route_ms,
    })

    # Step 4 — Model inference
    try:
        provider = get_provider(provider_name)
        result = with_retry(provider.call, safe_prompt)

        pipeline_trace.append({
            "step": "MODEL_INFERENCE",
            "status": "OK",
            "detail": f"{result['tokens_used']} tokens",
            "latency_ms": result["latency_ms"],
        })

        total_ms = round((time.perf_counter() - t_start) * 1000, 1)
        pipeline_trace.append({
            "step": "RESPONSE_STREAM",
            "status": "200 OK",
            "detail": "complete",
            "latency_ms": round(total_ms - sum(s["latency_ms"] for s in pipeline_trace[:-1]), 1),
        })

        log_request(
            request_id=request_id,
            prompt=safe_prompt,
            outcome="approved",
            metadata={
                "provider": provider_name,
                "model_name": result["model_name"],
                "classification": route["classification"],
                "pii_detected": gov["pii_detected"],
                "fallback_used": False,
                "tokens_used": result["tokens_used"],
                "total_latency_ms": total_ms,
                "pipeline_trace": pipeline_trace,
            }
        )

        return QueryResponse(
            response=result["text"],
            model_used=provider_name,
            policy_checked=True,
            request_id=request_id,
            classification=route["classification"],
            fallback_used=False
        )

    except Exception:
        try:
            fallback_name = route["fallback"]
            provider = get_provider(fallback_name)
            result = with_retry(provider.call, safe_prompt)

            pipeline_trace.append({
                "step": "MODEL_INFERENCE",
                "status": "FALLBACK",
                "detail": f"{fallback_name} — {result['tokens_used']} tokens",
                "latency_ms": result["latency_ms"],
            })

            total_ms = round((time.perf_counter() - t_start) * 1000, 1)
            pipeline_trace.append({
                "step": "RESPONSE_STREAM",
                "status": "200 OK",
                "detail": "complete (fallback)",
                "latency_ms": round(total_ms - sum(s["latency_ms"] for s in pipeline_trace[:-1]), 1),
            })

            log_request(
                request_id=request_id,
                prompt=safe_prompt,
                outcome="approved",
                metadata={
                    "provider": fallback_name,
                    "model_name": result["model_name"],
                    "classification": route["classification"],
                    "pii_detected": gov["pii_detected"],
                    "fallback_used": True,
                    "tokens_used": result["tokens_used"],
                    "total_latency_ms": total_ms,
                    "pipeline_trace": pipeline_trace,
                }
            )

            return QueryResponse(
                response=result["text"],
                model_used=fallback_name,
                policy_checked=True,
                request_id=request_id,
                classification=route["classification"],
                fallback_used=True
            )

        except Exception as fallback_error:
            total_ms = round((time.perf_counter() - t_start) * 1000, 1)
            pipeline_trace.append({
                "step": "MODEL_INFERENCE",
                "status": "ERROR",
                "detail": str(fallback_error),
                "latency_ms": total_ms,
            })

            log_request(
                request_id=request_id,
                prompt=safe_prompt,
                outcome="error",
                metadata={
                    "error": str(fallback_error),
                    "total_latency_ms": total_ms,
                    "pipeline_trace": pipeline_trace,
                }
            )
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail={
                    "error": str(fallback_error),
                    "request_id": request_id
                }
            )

# -----------------------------
# UI static assets (production)
# -----------------------------
# Mounted last so all API routes above take precedence.
# In local dev the directory may be absent, so the mount is conditional.
UI_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(UI_DIR):
    @app.get("/", include_in_schema=False)
    def serve_ui_root():
        return FileResponse(os.path.join(UI_DIR, "index.html"))

    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")