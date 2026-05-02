import sqlite3
import json
import os
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

AUDIT_BACKEND = os.getenv("AUDIT_BACKEND", "sqlite")
DB_PATH = os.getenv("AUDIT_DB_PATH", "audit.db")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# Approximate cost per 1K tokens by provider
COST_PER_1K_TOKENS = {
    "openai": 0.00015,
    "anthropic": 0.003,
    "vertex": 0.0001,
}


def compute_metrics(window_minutes: int = 60) -> dict:
    """
    Compute aggregate metrics from audit logs.
    Compares current window vs previous window for deltas.
    """
    if AUDIT_BACKEND == "firestore":
        return _compute_from_firestore(window_minutes)
    else:
        return _compute_from_sqlite(window_minutes)


def _compute_from_sqlite(window_minutes: int) -> dict:
    now = datetime.now(timezone.utc)
    current_start = (now - timedelta(minutes=window_minutes)).isoformat()
    previous_start = (now - timedelta(minutes=window_minutes * 2)).isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    current_rows = conn.execute(
        "SELECT * FROM audit_log WHERE timestamp >= ? ORDER BY timestamp DESC",
        (current_start,)
    ).fetchall()

    previous_rows = conn.execute(
        "SELECT * FROM audit_log WHERE timestamp >= ? AND timestamp < ? ORDER BY timestamp DESC",
        (previous_start, current_start)
    ).fetchall()

    conn.close()

    current = _analyze_rows(current_rows, window_minutes)
    previous = _analyze_rows(previous_rows, window_minutes)

    return _build_response(current, previous)


def _compute_from_firestore(window_minutes: int) -> dict:
    from google.cloud import firestore

    now = datetime.now(timezone.utc)
    current_start = (now - timedelta(minutes=window_minutes)).isoformat()
    previous_start = (now - timedelta(minutes=window_minutes * 2)).isoformat()

    db = firestore.Client(project=GCP_PROJECT_ID, database="default")
    collection = db.collection("audit_logs")

    current_docs = collection.where(
        "timestamp", ">=", current_start
    ).stream()
    current_rows = [doc.to_dict() for doc in current_docs]

    previous_docs = collection.where(
        "timestamp", ">=", previous_start
    ).where(
        "timestamp", "<", current_start
    ).stream()
    previous_rows = [doc.to_dict() for doc in previous_docs]

    return _build_response(
        _analyze_dicts(current_rows, window_minutes),
        _analyze_dicts(previous_rows, window_minutes),
    )


def _analyze_rows(rows, window_minutes: int) -> dict:
    """Analyze SQLite Row objects."""
    total = len(rows)
    approved = 0
    blocked = 0
    errors = 0
    latencies = []
    total_cost = 0.0
    total_tokens = 0
    providers = set()
    pii_count = 0

    for row in rows:
        entry = dict(row)
        outcome = entry.get("outcome", "")
        metadata = json.loads(entry["metadata"]) if entry.get("metadata") else {}

        if outcome == "approved":
            approved += 1
        elif outcome == "blocked":
            blocked += 1
        else:
            errors += 1

        if metadata.get("total_latency_ms"):
            latencies.append(metadata["total_latency_ms"])

        provider = metadata.get("provider", "")
        if provider:
            providers.add(provider)

        tokens = metadata.get("tokens_used", 0)
        if tokens:
            total_tokens += tokens
            if provider:
                cost_rate = COST_PER_1K_TOKENS.get(provider, 0.001)
                total_cost += (tokens / 1000) * cost_rate

        if metadata.get("pii_detected"):
            pii_count += 1

    return _summarize(total, approved, blocked, errors, latencies, total_cost, total_tokens, providers, pii_count, window_minutes)


def _analyze_dicts(rows: list[dict], window_minutes: int) -> dict:
    """Analyze Firestore dict objects."""
    total = len(rows)
    approved = 0
    blocked = 0
    errors = 0
    latencies = []
    total_cost = 0.0
    total_tokens = 0
    providers = set()
    pii_count = 0

    for entry in rows:
        outcome = entry.get("outcome", "")
        metadata = entry.get("metadata", {})

        if outcome == "approved":
            approved += 1
        elif outcome == "blocked":
            blocked += 1
        else:
            errors += 1

        if metadata.get("total_latency_ms"):
            latencies.append(metadata["total_latency_ms"])

        provider = metadata.get("provider", "")
        if provider:
            providers.add(provider)

        tokens = metadata.get("tokens_used", 0)
        if tokens:
            total_tokens += tokens
            if provider:
                cost_rate = COST_PER_1K_TOKENS.get(provider, 0.001)
                total_cost += (tokens / 1000) * cost_rate

        if metadata.get("pii_detected"):
            pii_count += 1

    return _summarize(total, approved, blocked, errors, latencies, total_cost, total_tokens, providers, pii_count, window_minutes)


def _summarize(total, approved, blocked, errors, latencies, total_cost, total_tokens, providers, pii_count, window_minutes) -> dict:
    rps = round(total / (window_minutes * 60), 4) if window_minutes > 0 else 0
    success_rate = round((approved / total) * 100, 1) if total > 0 else 0.0

    latencies_sorted = sorted(latencies)
    if latencies_sorted:
        p95_idx = int(len(latencies_sorted) * 0.95)
        p95 = round(latencies_sorted[min(p95_idx, len(latencies_sorted) - 1)], 1)
    else:
        p95 = 0.0

    cost_per_req = round(total_cost / total, 8) if total > 0 else 0.0

    return {
        "total": total,
        "approved": approved,
        "blocked": blocked,
        "errors": errors,
        "requests_per_second": rps,
        "success_rate": success_rate,
        "p95_latency_ms": p95,
        "cost_per_request": cost_per_req,
        "active_models": len(providers),
        "providers": list(providers),
        "total_tokens": total_tokens,
        "pii_detected_count": pii_count,
    }


def _delta(current_val, previous_val) -> str:
    if previous_val == 0:
        return "+0.0%" if current_val == 0 else "+100.0%"
    change = ((current_val - previous_val) / previous_val) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{round(change, 1)}%"


def _build_response(current: dict, previous: dict) -> dict:
    return {
        "requests_per_second": current["requests_per_second"],
        "success_rate": current["success_rate"],
        "p95_latency_ms": current["p95_latency_ms"],
        "cost_per_request": current["cost_per_request"],
        "active_models": current["active_models"],
        "providers": current["providers"],
        "total_tokens": current["total_tokens"],
        "total_requests": current["total"],
        "approved": current["approved"],
        "blocked": current["blocked"],
        "errors": current["errors"],
        "pii_detected_count": current["pii_detected_count"],
        "deltas": {
            "requests_per_second": _delta(current["requests_per_second"], previous["requests_per_second"]),
            "success_rate": _delta(current["success_rate"], previous["success_rate"]),
            "p95_latency_ms": _delta(current["p95_latency_ms"], previous["p95_latency_ms"]),
            "cost_per_request": _delta(current["cost_per_request"], previous["cost_per_request"]),
            "active_models": _delta(current["active_models"], previous["active_models"]),
            "total_tokens": _delta(current["total_tokens"], previous["total_tokens"]),
        },
    }
