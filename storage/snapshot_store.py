from datetime import datetime

from storage.db import get_connection, init_db
from models.snapshot import Snapshot


def save_snapshot(snapshot: Snapshot) -> int:
    init_db()
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO snapshots (taken_at, data) VALUES (?, ?)",
        (snapshot.taken_at.isoformat(), snapshot.model_dump_json()),
    )
    conn.commit()
    snapshot_id = cursor.lastrowid
    conn.close()
    return snapshot_id
    
def get_all_snapshots() -> list[Snapshot]:
    init_db()
    conn = get_connection()
    rows = conn.execute("SELECT data FROM snapshots ORDER BY taken_at ASC").fetchall()
    conn.close()
    return[Snapshot.model_validate_json(row["data"]) for row in rows]


def get_latest_snapshot() -> Snapshot | None:
    snapshots = get_all_snapshots()
    return snapshots[-1] if snapshots else None