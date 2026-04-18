from pydantic import BaseModel
from typing import Optional


# -----------------------------
# Inbound request to the gateway
# -----------------------------
class QueryRequest(BaseModel):
    prompt: str
    user_id: str
    session_id: Optional[str] = None


# -----------------------------
# Outbound response from the gateway
# -----------------------------
class QueryResponse(BaseModel):
    response: Optional[str] = None
    model_used: Optional[str] = None
    policy_checked: bool = False
    request_id: Optional[str] = None