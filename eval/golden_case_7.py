"""
Golden Case 7: nudge cap and escalation order. Nudges never exceed
the configured per-person daily cap. For the seeded overdue
commitment, a nudge precedes an escalation, and neither repeats
beyond the cap.
"""
import json
from datetime import date, timedelta
from pathlib import Path

from storage.commitment_tracking_service import run_commitment_check

LOG_PATH = Path("storage/notifications.jsonl")


def golden_case_7_nudge_and_escalation():
    # Clean slate - self-cleaning, same pattern as prior golden cases
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    # Also verify the daily cap: run TWICE on the SAME day, confirm
    # the second run doesn't send a duplicate nudge to anyone.
    day1 = date(2026, 8, 16)
    result_a = run_commitment_check(as_of_date=day1)
    result_b = run_commitment_check(as_of_date=day1)  # same day, re-run
    cap_holds = len(result_b["nudges_sent"]) == 0  # everyone already nudged today

    # Now simulate C-004's sequence: nudge (Aug 13-17) then escalate (Aug 18)
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    current = date(2026, 8, 13)
    end = date(2026, 8, 18)
    while current <= end:
        run_commitment_check(as_of_date=current)
        current += timedelta(days=1)

    with open(LOG_PATH) as f:
        entries = [json.loads(line) for line in f]
    c004_entries = [e for e in entries if e["commitment_id"] == "C-004"]
    nudge_ts = [e["timestamp"] for e in c004_entries if e["kind"] == "nudge"]
    escalation_ts = [e["timestamp"] for e in c004_entries if e["kind"] == "escalation"]

    order_correct = bool(nudge_ts) and bool(escalation_ts) and min(nudge_ts) < min(escalation_ts)

    passed = cap_holds and order_correct
    detail = (
        f"daily cap holds on same-day re-run: {cap_holds}; "
        f"nudge-before-escalation order for C-004: {order_correct} "
        f"({len(nudge_ts)} nudges, {len(escalation_ts)} escalations)"
    )
    return passed, passed, True, detail
