import sqlite3
import json
import os
from datetime import datetime, timezone

# -----------------------------
# Database setup
# -----------------------------
DB_PATH = os.getenv("AUDIT_DB_PATH", "audit.db")

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
    Create the audit log table if it doesn't exist.
    Called once on startup.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()


def log_request(
    request_id: str,
    prompt: str,
    outcome: str,
    metadata: dict = None
):
    """
    Log a single request to the audit database.
    outcome: "approved", "blocked", "error"
    metadata: dict with governance, routing, model info
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO audit_log (request_id, timestamp, prompt, outcome, metadata)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            request_id,
            datetime.now(timezone.utc).isoformat(),
            prompt[:500],
            outcome,
            json.dumps(metadata) if metadata else None
        )
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 20) -> list:
    """
    Retrieve recent audit log entries.
    Used by the /audit endpoint.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT * FROM audit_log
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]