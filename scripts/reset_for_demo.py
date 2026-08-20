"""
Resets all accumulated test/dev-run state to a clean baseline
before recording the demo, so the recording shows genuine first-run
behavior (a fresh gap-detection proposal, a fresh promotion
proposal, etc.) rather than leftovers from earlier manual testing.

Does NOT touch most of seed_data/*.json (the committed sample data
itself) - EXCEPT seed_data/risk_log.json, which write-execution
testing can genuinely mutate (RiskLogAdapter.append_risk writes
directly to it), so it is restored from a tracked clean-template
copy. Everything else cleared is state our OWN runs accumulated:
  - the proposals table (SQLite)
  - storage/weekly_reports.jsonl (persisted weekly-report history)
  - storage/notifications.jsonl (nudge/escalation log)
  - storage/refused_meeting_outcomes.jsonl (P8 refusal log)
  - storage/llm_cache/ (cached LLM responses, so the demo shows a
    real model call rather than a stale cached one)

Run with: python3.11 scripts/reset_for_demo.py
"""
import shutil
import json
from pathlib import Path

from storage.db import get_connection, init_db


def reset_proposals_table():
    init_db()
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]
    conn.execute("DELETE FROM proposals")
    conn.commit()
    conn.close()
    print(f"Cleared {count} proposal(s) from the database.")


def reset_file(path_str: str, label: str):
    path = Path(path_str)
    if path.exists():
        path.unlink()
        print(f"Removed {label} ({path_str}).")
    else:
        print(f"{label} already absent ({path_str}) - nothing to do.")


def reset_llm_cache():
    cache_dir = Path("storage/llm_cache")
    if cache_dir.exists():
        count = len(list(cache_dir.glob("*.json")))
        shutil.rmtree(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"Cleared {count} cached LLM response(s).")
    else:
        print("LLM cache directory already absent - nothing to do.")


def reset_risk_log():
    """Real risk-log entries can be written during write-execution
    testing/demos (RiskLogAdapter.append_risk writes directly to
    seed_data/risk_log.json). This restores it to the clean,
    committed 3-entry baseline from a tracked template file, so
    repeated demo runs never accumulate extra entries."""
    template = Path("seed_data/risk_log.clean_template.json")
    target = Path("seed_data/risk_log.json")
    if not template.exists():
        print("WARNING: seed_data/risk_log.clean_template.json not found - risk log NOT reset.")
        return
    with open(template) as f:
        data = json.load(f)
    count = len(data["risks"])
    shutil.copy(template, target)
    print(f"Restored risk log to clean baseline ({count} entries).")


def main():
    print("=== Resetting demo state to a clean baseline ===\n")
    reset_proposals_table()
    reset_file("storage/weekly_reports.jsonl", "persisted weekly-report history")
    reset_file("storage/notifications.jsonl", "notification (nudge/escalation) log")
    reset_file("storage/refused_meeting_outcomes.jsonl", "meeting-outcome refusal log")
    reset_llm_cache()
    reset_risk_log()
    print("\nDone. seed_data/*.json was NOT touched - only accumulated run state was cleared.")


if __name__ == "__main__":
    main()
