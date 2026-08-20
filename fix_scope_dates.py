import json
from datetime import datetime, timedelta

with open("seed_data/tracker_items.json") as f:
    data = json.load(f)

SPRINT_2_START = datetime(2026, 8, 17)
fixed = []

for item in data["items"]:
    created = datetime.fromisoformat(item["created_at"])

    # T-018: was meant to be ordinary Sprint 2 scope, not a
    # deliberate mid-sprint addition. Correct it to the sprint's
    # actual start day.
    if item["id"] == "T-018":
        item["created_at"] = "2026-08-17T09:00:00"
        fixed.append((item["id"], str(created), item["created_at"]))
        continue

    # T-019/T-020 are the ONLY deliberate mid-sprint-addition
    # difficulty - leave them untouched.
    if item["id"] in ("T-019", "T-020"):
        continue

    # Any bulk-generated item (T-021+) that coincidentally landed
    # on/after sprint start dilutes that signal - move it back
    # into Sprint 1's real range, preserving its time-of-day.
    if created >= SPRINT_2_START:
        new_created = created - timedelta(days=14)
        item["created_at"] = new_created.isoformat()
        fixed.append((item["id"], str(created), item["created_at"]))

with open("seed_data/tracker_items.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Fixed {len(fixed)} items:")
for item_id, old, new in fixed:
    print(f"  {item_id}: {old} -> {new}")
