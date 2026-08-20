import json
from datetime import datetime
from pathlib import Path

STORE_PATH = Path("storage/weekly_reports.jsonl")


def save_weekly_report_facts(facts_dict: dict) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORE_PATH, "a") as f:
        f.write(json.dumps(facts_dict) + "\n")


def get_latest_weekly_report_facts() -> dict | None:
    """Returns the most recently persisted weekly report's facts,
    or None if none exist yet - the honest 'no prior report'
    case, not a fabricated baseline."""
    if not STORE_PATH.exists():
        return None
    with open(STORE_PATH) as f:
        lines = [json.loads(line) for line in f if line.strip()]
    return lines[-1] if lines else None
