import uuid
from fastapi import FastAPI
from models import QueryRequest, QueryResponse

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
# Query endpoint (skeleton)
# Week 4: replace placeholder with real model call
# Week 5: add routing logic
# Week 6: add policy + PII check
# -----------------------------
@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    request_id = str(uuid.uuid4())

    # Placeholder — no model call yet
    return QueryResponse(
        response="Placeholder response - model not yet connected",
        model_used=None,
        policy_checked=False,
        request_id=request_id
    )