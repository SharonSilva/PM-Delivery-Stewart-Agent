import json
from datetime import datetime
from pathlib import Path


def log_refusal(meeting_id: str, reason: str) -> None:
    """Inspectable, append-only log of refused meeting outcomes.
    Never silently dropped - matches the notification-log pattern
    from P1 (inspectable local log, not a real external write)."""
    path = Path("storage/refused_meeting_outcomes.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "meeting_id": meeting_id,
        "reason": reason,
        "refused_at": datetime.now().isoformat(),
    }
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
