import sqlite3
import json
import os
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# -----------------------------
# Config
# -----------------------------
AUDIT_BACKEND = os.getenv("AUDIT_BACKEND", "sqlite")
DB_PATH = os.getenv("AUDIT_DB_PATH", "audit.db")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
FIRESTORE_COLLECTION = "audit_logs"

# -----------------------------
# SQLite setup
# -----------------------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id  TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    prompt      TEXT NOT NULL,
    outcome     TEXT NOT NULL,
    metadata    TEXT
)
"""

def init_db():
    """
    Initialise storage backend on startup.
    SQLite: creates table if not exists.
    Firestore: no init needed, collection created on first write.
    """
    if AUDIT_BACKEND == "sqlite":
        conn = sqlite3.connect(DB_PATH)
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
        conn.close()
        logger.info(f"Audit backend: SQLite ({DB_PATH})")
    else:
        logger.info(f"Audit backend: Firestore (project={GCP_PROJECT_ID})")


# -----------------------------
# Write log entry
# -----------------------------
def log_request(
    request_id: str,
    prompt: str,
    outcome: str,
    metadata: dict = None
):
    """
    Log a single request to the audit backend.
    outcome: "approved", "blocked", "error"
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if AUDIT_BACKEND == "firestore":
        _log_to_firestore(request_id, timestamp, prompt, outcome, metadata)
    else:
        _log_to_sqlite(request_id, timestamp, prompt, outcome, metadata)


def _log_to_sqlite(request_id, timestamp, prompt, outcome, metadata):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO audit_log (request_id, timestamp, prompt, outcome, metadata)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            request_id,
            timestamp,
            prompt[:500],
            outcome,
            json.dumps(metadata) if metadata else None
        )
    )
    conn.commit()
    conn.close()


def _log_to_firestore(request_id, timestamp, prompt, outcome, metadata):
    from google.cloud import firestore
    db = firestore.Client(project=GCP_PROJECT_ID, database="default")
    db.collection(FIRESTORE_COLLECTION).document(request_id).set({
        "request_id": request_id,
        "timestamp": timestamp,
        "prompt": prompt[:500],
        "outcome": outcome,
        "metadata": metadata or {}
    })


# -----------------------------
# Read log entries
# -----------------------------
def get_recent_logs(limit: int = 20) -> list:
    """
    Retrieve recent audit log entries.
    """
    if AUDIT_BACKEND == "firestore":
        return _get_logs_from_firestore(limit)
    else:
        return _get_logs_from_sqlite(limit)


def _get_logs_from_sqlite(limit):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    logs = []
    for row in rows:
        entry = dict(row)
        ordered_entry = {
            "id": entry["id"],
            "request_id": entry["request_id"],
            "timestamp": entry["timestamp"],
            "timestamp_pt": _convert_to_pt(entry["timestamp"]),
            "prompt": entry["prompt"],
            "outcome": entry["outcome"],
            "metadata": json.loads(entry["metadata"]) if entry.get("metadata") else {}
        }
        logs.append(ordered_entry)
    return logs


def _get_logs_from_firestore(limit):
    from google.cloud import firestore
    db = firestore.Client(project=GCP_PROJECT_ID, database="default")
    docs = (
        db.collection(FIRESTORE_COLLECTION)
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [doc.to_dict() for doc in docs]


# -----------------------------
# Get single log by request_id
# -----------------------------
def get_log_by_request_id(request_id: str) -> dict | None:
    if AUDIT_BACKEND == "firestore":
        return _get_log_by_id_firestore(request_id)
    else:
        return _get_log_by_id_sqlite(request_id)


def _get_log_by_id_sqlite(request_id: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM audit_log WHERE request_id = ? LIMIT 1",
        (request_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    entry = dict(row)
    return {
        "id": entry["id"],
        "request_id": entry["request_id"],
        "timestamp": entry["timestamp"],
        "timestamp_pt": _convert_to_pt(entry["timestamp"]),
        "prompt": entry["prompt"],
        "outcome": entry["outcome"],
        "metadata": json.loads(entry["metadata"]) if entry.get("metadata") else {}
    }


def _get_log_by_id_firestore(request_id: str) -> dict | None:
    from google.cloud import firestore
    db = firestore.Client(project=GCP_PROJECT_ID, database="default")
    doc = db.collection(FIRESTORE_COLLECTION).document(request_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()


# -----------------------------
# Convert timestamp to PT
# -----------------------------
def _convert_to_pt(utc_timestamp: str) -> str:
    """Convert UTC ISO timestamp to PT for display."""
    try:
        dt = datetime.fromisoformat(utc_timestamp)
        pt_offset = timedelta(hours=-7)  # PDT (UTC-7), use -8 for PST
        pt_time = dt + pt_offset
        return pt_time.strftime("%Y-%m-%d %I:%M:%S %p PT")
    except Exception:
        return utc_timestamp