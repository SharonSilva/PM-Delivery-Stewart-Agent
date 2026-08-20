import json
from datetime import date, timedelta
from pathlib import Path

from storage.commitment_tracking_service import run_commitment_check

# Clean slate - isolate this test from earlier debug runs
log_path = Path("storage/notifications.jsonl")
if log_path.exists():
    log_path.unlink()

# Simulate each day from just before C-004's due date through
# past the escalation threshold. C-004 (Jordan Lee) is due 2026-08-15,
# escalation threshold is 3 days overdue -> should escalate on 2026-08-18.
start = date(2026, 8, 13)
end = date(2026, 8, 18)
current = start

print("=== Day-by-day classification for C-004 (Jordan Lee) ===")
day_results = []
while current <= end:
    result = run_commitment_check(as_of_date=current)
    c004_entry = next(e for e in result["ageing_view"] if e["id"] == "C-004")
    nudged_today = any(n.commitment_id == "C-004" for n in result["nudges_sent"])
    escalated_today = any(e.commitment_id == "C-004" for e in result["escalations"])
    print(f"  {current}: classification={c004_entry['classification']}, nudged={nudged_today}, escalated={escalated_today}")
    day_results.append((current, c004_entry['classification'], nudged_today, escalated_today))
    current += timedelta(days=1)

print()
print("=== Full notification log for C-004, in order ===")
with open(log_path) as f:
    entries = [json.loads(line) for line in f]
c004_entries = [e for e in entries if e["commitment_id"] == "C-004"]
for e in c004_entries:
    print(f"  {e['timestamp']}: {e['kind']} -> {e['recipient']}")

# Verify: at least one nudge appears BEFORE the escalation, by timestamp
nudge_timestamps = [e["timestamp"] for e in c004_entries if e["kind"] == "nudge"]
escalation_timestamps = [e["timestamp"] for e in c004_entries if e["kind"] == "escalation"]

print()
if nudge_timestamps and escalation_timestamps:
    order_correct = min(nudge_timestamps) < min(escalation_timestamps)
    print(f"PASS: nudge before escalation, order correct: {order_correct}" if order_correct else "FAIL: order incorrect")
else:
    print(f"FAIL: missing nudge ({len(nudge_timestamps)}) or escalation ({len(escalation_timestamps)}) entries")
